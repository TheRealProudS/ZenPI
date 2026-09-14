#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "============================================================"
echo "           ZenPi Cockpit - Installationsassistent           "
echo "        Gehaertetes System nach BSI IT-Grundschutz          "
echo "============================================================"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[FEHLER] Bitte fuehre das Installationsskript als root oder mit sudo aus:${NC}"
  echo "sudo bash install.sh"
  exit 1
fi

INSTALL_DIR="/opt/zenpi"
CONFIG_DIR="/etc/zenpi"
LOG_DIR="/var/log/zenpi"

echo -e "${GREEN}[1/6] Installiere Systempakete (Python3, venv, gpiod, i2c-tools)...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip libgpiod2 gpiod i2c-tools curl sudo > /dev/null

echo -e "${GREEN}[2/6] Erstelle unprivilegierten Systembenutzer 'zenpi'...${NC}"
if ! id -u zenpi >/dev/null 2>&1; then
  useradd -r -s /bin/false -d "${INSTALL_DIR}" zenpi
fi

# Hardware-Gruppen zuweisen
usermod -a -G gpio,i2c,spi,video,dialout zenpi 2>/dev/null || true

echo -e "${GREEN}[3/6] Richte gehaertete Verzeichnisse ein...${NC}"
mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}" "${LOG_DIR}"
cp -r ./* "${INSTALL_DIR}/"

chown -R zenpi:zenpi "${INSTALL_DIR}" "${CONFIG_DIR}" "${LOG_DIR}"
chmod 750 "${INSTALL_DIR}"
chmod 700 "${CONFIG_DIR}" "${LOG_DIR}"

echo -e "${GREEN}[4/6] Erstelle Python Virtual Environment...${NC}"
python3 -m venv "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --quiet --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install --quiet -r "${INSTALL_DIR}/backend/requirements.txt"
chown -R zenpi:zenpi "${INSTALL_DIR}/venv"

echo -e "${GREEN}[5/6] Richte Least-Privilege Sudoers-Regeln fuer System-Dienste ein...${NC}"
cat << 'EOF' > /etc/sudoers.d/zenpi
zenpi ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active *, /usr/bin/systemctl start *, /usr/bin/systemctl stop *, /usr/bin/systemctl restart *, /usr/bin/vcgencmd *
EOF
chmod 440 /etc/sudoers.d/zenpi

echo -e "${GREEN}[6/6] Installiere und starte gehaerteten systemd-Dienst 'zenpi.service'...${NC}"
cp "${INSTALL_DIR}/deploy/zenpi.service" /etc/systemd/system/zenpi.service
systemctl daemon-reload
systemctl enable zenpi.service
systemctl restart zenpi.service

IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${CYAN}"
echo "============================================================"
echo -e "${GREEN}  ZenPi Cockpit erfolgreich gehaertet installiert!${CYAN}"
echo "============================================================"
echo -e "${NC}"
echo -e "Erreichbar im Browser ueber:"
echo -e "  - ${CYAN}http://${IP_ADDR}:8443${NC}"
echo -e "  - ${CYAN}http://raspberrypi.local:8443${NC}"
echo ""
echo -e "${YELLOW}WICHTIG (BSI IT-Grundschutz):${NC}"
echo "Beim ersten Aufruf im Browser wirst du aufgefordert, dein persoenliches"
echo "Administrator-Passwort fuer dieses Geraet festzulegen."
echo ""
echo -e "Status pruefen: sudo systemctl status zenpi"
echo -e "Audit-Logs:     sudo cat ${LOG_DIR}/audit.log"
echo ""
