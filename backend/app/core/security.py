import os
import json
import time
import hmac
import hashlib
from pathlib import Path
from typing import Optional, Dict
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

SECURITY_FILE = Path(os.getenv("ZENPI_CONFIG_PATH", Path(__file__).resolve().parent.parent.parent / "config.json"))
AUDIT_LOG_FILE = Path(settings.log_dir) / "audit.log"

active_sessions: Dict[str, float] = {}
rate_limit_tracker: Dict[str, list] = {}

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{derived.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, derived_hex = stored_hash.split(":", 1)
    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(derived_hex, new_hash)

def load_stored_credentials() -> Dict[str, str]:
    if SECURITY_FILE.exists():
        try:
            with open(SECURITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "admin_hash": settings.admin_password_hash or hash_password("zenpi-admin-init"),
        "initial_setup_required": not bool(settings.admin_password_hash)
    }

def save_stored_credentials(data: Dict[str, str]):
    SECURITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SECURITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def audit_log(event_type: str, ip: str, detail: str):
    masked_ip = ":".join(ip.split(":")[:2]) if ":" in ip else ".".join(ip.split(".")[:2]) + ".*.*"
    entry = {
        "timestamp": int(time.time()),
        "event": event_type,
        "client": masked_ip,
        "detail": detail
    }
    try:
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def check_rate_limit(client_ip: str):
    now = time.time()
    if client_ip not in rate_limit_tracker:
        rate_limit_tracker[client_ip] = []
    
    rate_limit_tracker[client_ip] = [t for t in rate_limit_tracker[client_ip] if now - t < 60]
    
    if len(rate_limit_tracker[client_ip]) >= settings.rate_limit_requests:
        audit_log("RATE_LIMIT_EXCEEDED", client_ip, "Blocked temporary")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    rate_limit_tracker[client_ip].append(now)

def require_auth(request: Request, creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)):
    if not settings.auth_enabled:
        return True
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_rate_limit(client_ip)

    token = None
    if creds:
        token = creds.credentials
    elif "zenpi_session" in request.cookies:
        token = request.cookies.get("zenpi_session")

    if not token or token not in active_sessions:
        audit_log("UNAUTHORIZED_ACCESS", client_ip, request.url.path)
        raise HTTPException(status_code=401, detail="Authentication required")

    session_time = active_sessions[token]
    if time.time() - session_time > 86400:
        del active_sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")

    return True
