import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
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
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GpioToggleRequest(BaseModel):
    bcm: int
    state: int

class GpioModeRequest(BaseModel):
    bcm: int
    mode: str

class ServiceActionRequest(BaseModel):
    service_name: str
    action: str

@app.get("/api/system/telemetry")
def api_telemetry():
    return get_system_telemetry()

@app.get("/api/gpio/pins")
def api_gpio_pins():
    return get_gpio_status_list()

@app.post("/api/gpio/toggle")
def api_gpio_toggle(req: GpioToggleRequest):
    ok = set_gpio_state(req.bcm, req.state)
    if not ok:
        raise HTTPException(status_code=400, detail="Ungültiger BCM Pin")
    return {"status": "success", "bcm": req.bcm, "state": req.state}

@app.post("/api/gpio/mode")
def api_gpio_mode(req: GpioModeRequest):
    ok = set_gpio_mode(req.bcm, req.mode)
    if not ok:
        raise HTTPException(status_code=400, detail="Ungültiger Modus")
    return {"status": "success", "bcm": req.bcm, "mode": req.mode}

@app.get("/api/hardware/i2c")
def api_i2c_scan():
    return scan_i2c_bus(1)

@app.get("/api/hardware/onewire")
def api_onewire_scan():
    return scan_onewire_sensors()

@app.get("/api/services")
def api_services():
    return list_services()

@app.post("/api/services/action")
def api_service_action(req: ServiceActionRequest):
    ok = control_service(req.service_name, req.action)
    return {"status": "success" if ok else "failed", "service": req.service_name, "action": req.action}

@app.get("/api/docker/containers")
def api_docker_containers():
    return list_docker_containers()

@app.get("/api/network/interfaces")
def api_network_interfaces():
    return get_network_interfaces()

@app.get("/api/network/wifi/scan")
def api_wifi_scan():
    return scan_wifi_networks()

@app.get("/api/pi/config")
def api_pi_config():
    return get_pi_config_overview()

@app.get("/api/camera/stream")
def api_camera_stream():
    return StreamingResponse(
        mjpeg_stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/snapshot")
def api_camera_snapshot():
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
        file_path = frontend_dir / full_path
        if file_path.is_file():
            return HTMLResponse(file_path.read_text(encoding="utf-8"))
        return HTMLResponse((frontend_dir / "index.html").read_text(encoding="utf-8"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
