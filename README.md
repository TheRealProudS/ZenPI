# ZenPi Cockpit

Modernes, ressourcenschonendes All-in-One Web-Management-System für den Raspberry Pi und Debian Linux. Entwickelt von Zenkner-Technology.

![ZenPi Logo](assets/zenpi_logo.png)

---

## Highlights & Features

- **Live-Telemetrie**: SoC-Temperatur, Taktfrequenzen (ARM & GPU), RAM, Swap, CPU-Last und Throttling-Radar (`vcgencmd get_throttled` zur Erkennung von Unterspannung).
- **Interaktives 40-Pin GPIO Pinout**: Visuelle Matrix mit BCM/Board-Umschaltung, Pegel-Monitor und Klick-to-Toggle für Relais und LEDs.
- **Hardware-Bus-Scanner**: Direkter I2C-Scanner (`i2cdetect`), SPI-Prüfung und automatische Erkennung von 1-Wire Temperatursensoren (DS18B20).
- **Kamera-Streaming**: Live-Stream für offizielle Raspberry Pi Cams (CSI / `libcamera`) und USB-Webcams inklusive Schnappschussfunktion.
- **Raspberry Pi OS Tweaker**: Hostname, Schnittstellen (SSH, VNC, I2C, SPI), Boot-Modus und Audio-Ausgang im Browser steuern.
- **Dienste & Container Hub**: 1-Klick-Steuerung für beliebte Homelab-Dienste (Pi-hole, WireGuard, Plex, Nginx, Home Assistant) und Docker-Container.
- **Speicher & SD-Karten-Backup**: Partitionsübersicht, I/O-Aktivität und 1-Klick-SD-Image-Backup im laufenden Betrieb.
- **WLAN- & Netzwerk-Manager**: 2.4/5 GHz WLAN-Scan, IP-Übersicht und Notfall-Access-Point-Modus.
- **Integrierte Web-Shell & Logs**: Schneller Konsolen-Zugriff und strukturierter `journalctl`-Viewer.

---

## 1-Befehl-Installation (Raspberry Pi)

Auf dem Raspberry Pi im Terminal oder per SSH ausführen:

```bash
curl -sSL https://zenkner-technology.de/zenpi/install.sh | bash
```

Nach der Installation ist das Web-Dashboard sofort im lokalen Netzwerk erreichbar:
`http://raspberrypi.local:8443` oder `http://<PI-IP>:8443`

---

## Manuelle Installation & Entwicklung

### Voraussetzungen
- Python 3.10+
- Linux (Raspberry Pi OS / Debian) oder Windows/macOS (automatischer Mock-/Simulationsmodus)

```bash
# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r backend/requirements.txt

# Server starten
python backend/app/main.py
```

Das Cockpit startet standardmäßig auf Port `8443`.

---

## Lizenz

ZenPi Non-Commercial Software License (ZNC-1.0)

- **Private Nutzung & Modifikation**: Kostenfrei für persönliche, private und Bildungszwecke gestattet.
- **Kommerzielle Nutzung**: Eine kommerzielle Nutzung, Verwertung oder Integration ist vorab mit dem Entwickler abzustimmen.
- Kontakt: `cyrill-pascal.zenkner@zenkner-technology.de` | [Zenkner-Technology](https://www.zenkner-technology.de)

Details siehe [LICENSE](LICENSE).
