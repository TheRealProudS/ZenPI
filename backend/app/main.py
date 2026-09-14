import os
import sys
import secrets
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import (
    require_auth, hash_password, verify_password,
    load_stored_credentials, save_stored_credentials,
    audit_log, active_sessions
)
from app.hardware.pi_sensors import get_system_telemetry, get_throttled_status
from app.hardware.pinout_data import (
    get_gpio_status_list, set_gpio_state, set_gpio_mode,
    scan_i2c_bus, scan_onewire_sensors
)
from app.api.services import list_services, control_service, list_docker_containers
from app.api.network_config import get_network_interfaces, scan_wifi_networks, get_pi_config_overview
from app.api.camera import mjpeg_stream_generator, generate_mock_frame

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url=None,
    redoc_url=None
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:;"
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)

class SetupRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)

class GpioToggleRequest(BaseModel):
    bcm: int = Field(ge=0, le=40)
    state: int = Field(ge=0, le=1)

class GpioModeRequest(BaseModel):
    bcm: int = Field(ge=0, le=40)
    mode: str = Field(pattern="^(in|out)$")

class ServiceActionRequest(BaseModel):
    service_name: str = Field(pattern="^[a-zA-Z0-9_-]+$")
    action: str = Field(pattern="^(start|stop|restart)$")

@app.get("/api/auth/status")
def api_auth_status(request: Request):
    creds = load_stored_credentials()
    token = request.cookies.get("zenpi_session")
    is_authenticated = bool(token and token in active_sessions)
    return {
        "auth_enabled": settings.auth_enabled,
        "initial_setup_required": creds.get("initial_setup_required", False),
        "is_authenticated": is_authenticated
    }

@app.post("/api/auth/setup")
def api_auth_setup(req: SetupRequest, request: Request):
    creds = load_stored_credentials()
    if not creds.get("initial_setup_required", False):
        raise HTTPException(status_code=400, detail="Initial setup already completed")
    
    creds["admin_hash"] = hash_password(req.new_password)
    creds["initial_setup_required"] = False
    save_stored_credentials(creds)
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_log("ADMIN_PASSWORD_SET", client_ip, "Initial administrator account initialized")
    
    token = secrets.token_hex(32)
    active_sessions[token] = time.time() if "time" in globals() else 1.0
    import time as _t
    active_sessions[token] = _t.time()
    
    resp = JSONResponse(content={"status": "success", "token": token})
    resp.set_cookie(
        key="zenpi_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400
    )
    return resp

@app.post("/api/auth/login")
def api_auth_login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    creds = load_stored_credentials()
    stored_hash = creds.get("admin_hash", "")
    
    if not verify_password(req.password, stored_hash):
        audit_log("LOGIN_FAILED", client_ip, "Invalid password attempt")
        raise HTTPException(status_code=401, detail="Ungueltiges Kennwort")
    
    token = secrets.token_hex(32)
    import time as _t
    active_sessions[token] = _t.time()
    audit_log("LOGIN_SUCCESS", client_ip, "Authenticated administrative session")
    
    resp = JSONResponse(content={"status": "success", "token": token})
    resp.set_cookie(
        key="zenpi_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400
    )
    return resp

@app.post("/api/auth/logout")
def api_auth_logout(request: Request):
    token = request.cookies.get("zenpi_session")
    if token and token in active_sessions:
        del active_sessions[token]
    resp = JSONResponse(content={"status": "logged_out"})
    resp.delete_cookie("zenpi_session")
    return resp

@app.get("/api/system/telemetry")
def api_telemetry(auth=Depends(require_auth)):
    return get_system_telemetry()

@app.get("/api/gpio/pins")
def api_gpio_pins(auth=Depends(require_auth)):
    return get_gpio_status_list()

@app.post("/api/gpio/toggle")
def api_gpio_toggle(req: GpioToggleRequest, request: Request, auth=Depends(require_auth)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    ok = set_gpio_state(req.bcm, req.state)
    if not ok:
        raise HTTPException(status_code=400, detail="Ungueltiger BCM Pin")
    audit_log("GPIO_TOGGLE", client_ip, f"BCM {req.bcm} -> {req.state}")
    return {"status": "success", "bcm": req.bcm, "state": req.state}

@app.post("/api/gpio/mode")
def api_gpio_mode(req: GpioModeRequest, request: Request, auth=Depends(require_auth)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    ok = set_gpio_mode(req.bcm, req.mode)
    if not ok:
        raise HTTPException(status_code=400, detail="Ungueltiger Modus")
    audit_log("GPIO_MODE", client_ip, f"BCM {req.bcm} -> {req.mode}")
    return {"status": "success", "bcm": req.bcm, "mode": req.mode}

@app.get("/api/hardware/i2c")
def api_i2c_scan(auth=Depends(require_auth)):
    return scan_i2c_bus(1)

@app.get("/api/hardware/onewire")
def api_onewire_scan(auth=Depends(require_auth)):
    return scan_onewire_sensors()

@app.get("/api/services")
def api_services(auth=Depends(require_auth)):
    return list_services()

@app.post("/api/services/action")
def api_service_action(req: ServiceActionRequest, request: Request, auth=Depends(require_auth)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    ok = control_service(req.service_name, req.action)
    audit_log("SERVICE_CONTROL", client_ip, f"{req.service_name} -> {req.action} (result: {ok})")
    return {"status": "success" if ok else "failed", "service": req.service_name, "action": req.action}

@app.get("/api/docker/containers")
def api_docker_containers(auth=Depends(require_auth)):
    return list_docker_containers()

@app.get("/api/network/interfaces")
def api_network_interfaces(auth=Depends(require_auth)):
    return get_network_interfaces()

@app.get("/api/network/wifi/scan")
def api_wifi_scan(auth=Depends(require_auth)):
    return scan_wifi_networks()

@app.get("/api/pi/config")
def api_pi_config(auth=Depends(require_auth)):
    return get_pi_config_overview()

@app.get("/api/camera/stream")
def api_camera_stream(auth=Depends(require_auth)):
    return StreamingResponse(
        mjpeg_stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/snapshot")
def api_camera_snapshot(auth=Depends(require_auth)):
    frame = generate_mock_frame()
    return Response(content=frame, media_type="image/jpeg")

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_system_telemetry()
            await websocket.send_json(data)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if (frontend_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "public")), name="static")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path:
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)
        return FileResponse(frontend_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
