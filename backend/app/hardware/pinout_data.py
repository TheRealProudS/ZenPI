import os
import subprocess
from typing import Dict, List, Any

# 40-Pin Header Definition für Raspberry Pi (3, 4, 5, Zero 2W)
RPI_40_PIN_HEADER = [
    {"pin": 1, "name": "3.3V Power", "type": "power", "bcm": None},
    {"pin": 2, "name": "5V Power", "type": "power", "bcm": None},
    {"pin": 3, "name": "GPIO 2", "type": "gpio", "bcm": 2, "alt": "I2C1 SDA"},
    {"pin": 4, "name": "5V Power", "type": "power", "bcm": None},
    {"pin": 5, "name": "GPIO 3", "type": "gpio", "bcm": 3, "alt": "I2C1 SCL"},
    {"pin": 6, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 7, "name": "GPIO 4", "type": "gpio", "bcm": 4, "alt": "GPCLK0 / 1-Wire"},
    {"pin": 8, "name": "GPIO 14", "type": "gpio", "bcm": 14, "alt": "UART0 TXD"},
    {"pin": 9, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 10, "name": "GPIO 15", "type": "gpio", "bcm": 15, "alt": "UART0 RXD"},
    {"pin": 11, "name": "GPIO 17", "type": "gpio", "bcm": 17, "alt": None},
    {"pin": 12, "name": "GPIO 18", "type": "gpio", "bcm": 18, "alt": "PCM CLK / PWM0"},
    {"pin": 13, "name": "GPIO 27", "type": "gpio", "bcm": 27, "alt": None},
    {"pin": 14, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 15, "name": "GPIO 22", "type": "gpio", "bcm": 22, "alt": None},
    {"pin": 16, "name": "GPIO 23", "type": "gpio", "bcm": 23, "alt": None},
    {"pin": 17, "name": "3.3V Power", "type": "power", "bcm": None},
    {"pin": 18, "name": "GPIO 24", "type": "gpio", "bcm": 24, "alt": None},
    {"pin": 19, "name": "GPIO 10", "type": "gpio", "bcm": 10, "alt": "SPI0 MOSI"},
    {"pin": 20, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 21, "name": "GPIO 9", "type": "gpio", "bcm": 9, "alt": "SPI0 MISO"},
    {"pin": 22, "name": "GPIO 25", "type": "gpio", "bcm": 25, "alt": None},
    {"pin": 23, "name": "GPIO 11", "type": "gpio", "bcm": 11, "alt": "SPI0 SCLK"},
    {"pin": 24, "name": "GPIO 8", "type": "gpio", "bcm": 8, "alt": "SPI0 CE0"},
    {"pin": 25, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 26, "name": "GPIO 7", "type": "gpio", "bcm": 7, "alt": "SPI0 CE1"},
    {"pin": 27, "name": "ID_SD", "type": "id_eeprom", "bcm": 0, "alt": "I2C ID EEPROM"},
    {"pin": 28, "name": "ID_SC", "type": "id_eeprom", "bcm": 1, "alt": "I2C ID EEPROM"},
    {"pin": 29, "name": "GPIO 5", "type": "gpio", "bcm": 5, "alt": None},
    {"pin": 30, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 31, "name": "GPIO 6", "type": "gpio", "bcm": 6, "alt": None},
    {"pin": 32, "name": "GPIO 12", "type": "gpio", "bcm": 12, "alt": "PWM0"},
    {"pin": 33, "name": "GPIO 13", "type": "gpio", "bcm": 13, "alt": "PWM1"},
    {"pin": 34, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 35, "name": "GPIO 19", "type": "gpio", "bcm": 19, "alt": "PCM FS / PWM1"},
    {"pin": 36, "name": "GPIO 16", "type": "gpio", "bcm": 16, "alt": None},
    {"pin": 37, "name": "GPIO 26", "type": "gpio", "bcm": 26, "alt": None},
    {"pin": 38, "name": "GPIO 20", "type": "gpio", "bcm": 20, "alt": "PCM DIN"},
    {"pin": 39, "name": "Ground", "type": "ground", "bcm": None},
    {"pin": 40, "name": "GPIO 21", "type": "gpio", "bcm": 21, "alt": "PCM DOUT"},
]

# Lokaler Zustandsspeicher für GPIO-Pins (für Mock & Live-Cache)
_gpio_state_cache: Dict[int, Dict[str, Any]] = {}

for p in RPI_40_PIN_HEADER:
    if p["bcm"] is not None:
        _gpio_state_cache[p["bcm"]] = {
            "mode": "OUTPUT" if p["bcm"] in (17, 27, 22) else "INPUT",
            "state": 0,
            "pwm": 0,
        }

def get_gpio_status_list() -> List[Dict[str, Any]]:
    pins = []
    for pin_info in RPI_40_PIN_HEADER:
        p = dict(pin_info)
        bcm = p["bcm"]
        if bcm is not None:
            cached = _gpio_state_cache.get(bcm, {"mode": "INPUT", "state": 0, "pwm": 0})
            p["mode"] = cached["mode"]
            p["state"] = cached["state"]
            p["pwm"] = cached["pwm"]
        else:
            p["mode"] = None
            p["state"] = None
            p["pwm"] = None
        pins.append(p)
    return pins

def set_gpio_state(bcm: int, state: int) -> bool:
    if bcm not in _gpio_state_cache:
        return False
    _gpio_state_cache[bcm]["state"] = 1 if state else 0
    _gpio_state_cache[bcm]["mode"] = "OUTPUT"
    
    # Echter gpiod Hardware-Befehl falls auf Pi vorhanden
    try:
        subprocess.run(["gpioset", "0", f"{bcm}={1 if state else 0}"], capture_output=True, timeout=1)
    except Exception:
        pass
    return True

def set_gpio_mode(bcm: int, mode: str) -> bool:
    if bcm not in _gpio_state_cache:
        return False
    mode = mode.upper()
    if mode in ("INPUT", "OUTPUT", "PWM"):
        _gpio_state_cache[bcm]["mode"] = mode
        return True
    return False

def scan_i2c_bus(bus: int = 1) -> List[Dict[str, Any]]:
    devices = []
    # Echter Scan via i2cdetect
    try:
        res = subprocess.run(["i2cdetect", "-y", str(bus)], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")[1:]
            for line in lines:
                parts = line.split(":")[1].split()
                for part in parts:
                    if part not in ("--", "UU"):
                        addr = "0x" + part
                        devices.append({"address": addr, "bus": bus, "description": get_known_i2c_device(addr)})
            return devices
    except Exception:
        pass
    
    # Mock-Devices für Tests & Demonstration
    return [
        {"address": "0x3c", "bus": bus, "description": "SSD1306 / SH1106 OLED Display (128x64)"},
        {"address": "0x76", "bus": bus, "description": "BMP280 / BME280 Klimasensor (Temp/Pressure/Hum)"},
        {"address": "0x68", "bus": bus, "description": "DS3231 Real Time Clock (RTC) / MPU6050 Gyro"},
    ]

def get_known_i2c_device(hex_addr: str) -> str:
    known = {
        "0x3c": "OLED Display SSD1306 (128x64)",
        "0x3d": "OLED Display SSD1306 (Alternative)",
        "0x76": "BMP280 / BME280 Barometer Sensor",
        "0x77": "BMP280 (Alt Address)",
        "0x68": "DS3231 RTC / MPU6050 6-Achsen Sensor",
        "0x48": "ADS1115 16-Bit ADC",
        "0x20": "PCF8574 I/O Expander",
        "0x27": "HD44780 LCD I2C Rucksack",
    }
    return known.get(hex_addr.lower(), "Unbekanntes I2C-Peripheriegerät")

def scan_onewire_sensors() -> List[Dict[str, Any]]:
    sensors = []
    base_dir = "/sys/bus/w1/devices/"
    if os.path.exists(base_dir):
        try:
            for item in os.listdir(base_dir):
                if item.startswith("28-"):
                    sensor_file = os.path.join(base_dir, item, "w1_slave")
                    if os.path.exists(sensor_file):
                        with open(sensor_file, "r") as f:
                            content = f.read()
                            if "YES" in content:
                                temp_line = content.split("t=")[-1].strip()
                                temp_c = round(float(temp_line) / 1000.0, 2)
                                sensors.append({"id": item, "model": "DS18B20", "temperature_c": temp_c})
            if sensors:
                return sensors
        except Exception:
            pass
    # Mock
    return [
        {"id": "28-00000abc1234", "model": "DS18B20", "temperature_c": 21.8},
        {"id": "28-00000fed5678", "model": "DS18B20", "temperature_c": 22.4}
    ]
