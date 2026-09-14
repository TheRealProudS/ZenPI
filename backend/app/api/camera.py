import io
import time
import math
from fastapi.responses import StreamingResponse

def generate_mock_frame() -> bytes:
    # Erzeugt ein simuliertes Testbild / Teststream falls keine echte Pi-Cam angeschlossen ist
    from PIL import Image, ImageDraw, ImageFont
    
    width, height = 640, 360
    img = Image.new("RGB", (width, height), color=(13, 20, 36))
    draw = ImageDraw.Draw(img)
    
    # Raster zeichnen
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(20, 35, 60), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(20, 35, 60), width=1)
        
    # Fadenkreuz & HUD
    cx, cy = width // 2, height // 2
    draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], outline=(56, 189, 248), width=2)
    draw.line([(cx - 70, cy), (cx + 70, cy)], fill=(56, 189, 248), width=1)
    draw.line([(cx, cy - 70), (cx, cy + 70)], fill=(56, 189, 248), width=1)
    
    # Text
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, 20), "ZENPI CAMERA STREAM [LIVE SIMULATOR]", fill=(56, 189, 248))
    draw.text((20, 45), f"TIME: {now_str}", fill=(241, 245, 249))
    draw.text((20, 65), "FPS: 30 | RES: 640x360 | SOURCE: CSI / LIB-CAMERA", fill=(148, 163, 184))
    
    # Animierter Sensor-Punkt
    t = time.time() * 2
    px = int(cx + math.cos(t) * 120)
    py = int(cy + math.sin(t) * 60)
    draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=(244, 63, 94))
    draw.text((px + 10, py - 6), "TRACK_TARGET_01", fill=(244, 63, 94))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

async def mjpeg_stream_generator():
    while True:
        frame = generate_mock_frame()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.08)  # ~12 FPS
