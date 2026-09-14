#!/bin/bash
set -e

# ZenPi 1-Befehl-Installationsskript für Raspberry Pi OS / Debian Linux
# Entwickelt von Zenkner-Technology (https://zenkner-technology.de)

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "============================================================"
echo "           ZenPi Cockpit - Installationsassistent           "
echo "           Zenkner-Technology Linux Suite                   "
echo "============================================================"
echo -e "${NC}"

# Root-Check
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[FEHLER] Bitte führe das Installationsskript als root oder mit sudo aus:${NC}"
  echo "sudo bash install.sh"
  exit 1
fi

INSTALL_DIR="/opt/zenpi"

echo -e "${GREEN}[1/5] Installiere Systempakete (Python3, venv, gpiod, i2c-tools)...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip libgpiod2 gpiod i2c-tools curl > /dev/null

echo -e "${GREEN}[2/5] Richte Zielverzeichnis ${INSTALL_DIR} ein...${NC}"
mkdir -p "${INSTALL_DIR}"
cp -r ./* "${INSTALL_DIR}/"

echo -e "${GREEN}[3/5] Erstelle Python Virtual Environment & installiere Requirements...${NC}"
python3 -m venv "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install --quiet -r "${INSTALL_DIR}/backend/requirements.txt"

echo -e "${GREEN}[4/5] Installiere und starte systemd Dienst 'zenpi.service'...${NC}"
cp "${INSTALL_DIR}/deploy/zenpi.service" /etc/systemd/system/zenpi.service
systemctl daemon-reload
systemctl enable zenpi.service
systemctl restart zenpi.service

IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${CYAN}"
echo "============================================================"
echo -e "${GREEN}  ✓ ZenPi Cockpit wurde erfolgreich installiert & gestartet!${CYAN}"
echo "============================================================"
echo -e "${NC}"
echo -e "Erreichbar im Browser über:"
echo -e "  👉  ${CYAN}http://${IP_ADDR}:8443${NC}"
echo -e "  👉  ${CYAN}http://raspberrypi.local:8443${NC}"
echo ""
echo -e "${YELLOW}Status prüfen:${NC} sudo systemctl status zenpi"
echo -e "${YELLOW}Logs ansehen:${NC}   sudo journalctl -u zenpi -f"
echo ""
