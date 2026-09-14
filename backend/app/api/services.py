import subprocess
import shutil
from typing import List, Dict, Any

POPULAR_SERVICES = [
    {"name": "ssh", "title": "SSH Server", "desc": "Sicherer Terminal-Fernzugriff"},
    {"name": "docker", "title": "Docker Daemon", "desc": "Container-Laufzeitumgebung"},
    {"name": "nginx", "title": "Nginx Webserver", "desc": "Reverse Proxy & Webserver"},
    {"name": "pihole-FTL", "title": "Pi-hole DNS", "desc": "Netzwerkweiter Ad-Blocker"},
    {"name": "wg-quick@wg0", "title": "WireGuard VPN", "desc": "Verschlüsseltes VPN-Gateway"},
    {"name": "home-assistant", "title": "Home Assistant", "desc": "Smart Home Steuerzentrale"},
    {"name": "mosquitto", "title": "Mosquitto MQTT", "desc": "IoT Message Broker"},
    {"name": "bluetooth", "title": "Bluetooth Daemon", "desc": "Drahtlos-Peripherie"},
]

_mock_service_states = {
    "ssh": "active",
    "docker": "active",
    "nginx": "active",
    "pihole-FTL": "active",
    "wg-quick@wg0": "inactive",
    "home-assistant": "inactive",
    "mosquitto": "active",
    "bluetooth": "active",
}

def get_service_status(service_name: str) -> str:
    if shutil.which("systemctl"):
        try:
            res = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True, timeout=2)
            return res.stdout.strip()
        except Exception:
            pass
    return _mock_service_states.get(service_name, "inactive")

def list_services() -> List[Dict[str, Any]]:
    result = []
    for s in POPULAR_SERVICES:
        name = s["name"]
        status = get_service_status(name)
        result.append({
            "name": name,
            "title": s["title"],
            "desc": s["desc"],
            "status": status,
            "is_active": status == "active",
        })
    return result

def control_service(service_name: str, action: str) -> bool:
    action = action.lower()
    if action not in ("start", "stop", "restart"):
        return False
    
    if shutil.which("systemctl"):
        try:
            res = subprocess.run(["sudo", "systemctl", action, service_name], capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception:
            pass
    
    if action == "start":
        _mock_service_states[service_name] = "active"
    elif action == "stop":
        _mock_service_states[service_name] = "inactive"
    elif action == "restart":
        _mock_service_states[service_name] = "active"
    return True

def list_docker_containers() -> List[Dict[str, Any]]:
    containers = []
    if shutil.which("docker"):
        try:
            res = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.State}}"],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    parts = line.split("|")
                    if len(parts) >= 5:
                        containers.append({
                            "id": parts[0],
                            "name": parts[1],
                            "image": parts[2],
                            "status": parts[3],
                            "state": parts[4],
                        })
                return containers
        except Exception:
            pass
    return [
        {"id": "c1a93e81", "name": "portainer-ce", "image": "portainer/portainer-ce:latest", "status": "Up 4 days", "state": "running"},
        {"id": "f82b7190", "name": "pihole", "image": "pihole/pihole:latest", "status": "Up 2 weeks", "state": "running"},
        {"id": "a3b4c5d6", "name": "vaultwarden", "image": "vaultwarden/server:latest", "status": "Exited (0) 2 hours ago", "state": "exited"},
    ]
