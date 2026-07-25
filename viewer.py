from flask import Flask, Response, render_template_string, request, jsonify
import pyrealsense2 as rs
import numpy as np
from PIL import Image, ImageDraw
import io
import time

app = Flask(__name__)

# RealSense Yapılandırması
pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.color, 640, 480, rs.format.yuyv, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

print("RealSense Viewer Başlatılıyor...")
profile = pipeline.start(config)

device = profile.get_device()
depth_sensor = device.first_depth_sensor()

if depth_sensor.supports(rs.option.frames_queue_sIze):
    depth_sensor.set_option(rs.option.frames_queue_sIze, 32)

# Saf Python YUYV -> RGB Dönüştürücü
def yuyv_to_rgb(raw_bytes, cw, ch):
    total_bytes = len(raw_bytes)
    calc_w = cw if cw > 0 else 640
    calc_h = total_bytes // (calc_w * 2)
    if calc_h == 0:
        calc_h = ch if ch > 0 else 480
        calc_w = total_bytes // (calc_h * 2)

    yuyv = raw_bytes.reshape((calc_h, calc_w // 2, 4))
    Y0, U, Y1, V = yuyv[:,:,0].astype(np.float32), yuyv[:,:,1].astype(np.float32)-128.0, yuyv[:,:,2].astype(np.float32), yuyv[:,:,3].astype(np.float32)-128.0

    R0 = np.clip(Y0 + 1.402 * V, 0, 255)
    G0 = np.clip(Y0 - 0.344136 * U - 0.714136 * V, 0, 255)
    B0 = np.clip(Y0 + 1.772 * U, 0, 255)
    R1 = np.clip(Y1 + 1.402 * V, 0, 255)
    G1 = np.clip(Y1 - 0.344136 * U - 0.714136 * V, 0, 255)
    B1 = np.clip(Y1 + 1.772 * U, 0, 255)

    rgb = np.zeros((calc_h, calc_w, 3), dtype=np.uint8)
    rgb[:, 0::2, 0], rgb[:, 0::2, 1], rgb[:, 0::2, 2] = R0, G0, B0
    rgb[:, 1::2, 0], rgb[:, 1::2, 1], rgb[:, 1::2, 2] = R1, G1, B1
    return rgb

# Saf Python Derinlik Renklendirme
def depth_to_colormap(depth_matrix):
    scaled = np.clip(depth_matrix * 0.04, 0, 255).astype(np.uint8)
    r = scaled
    g = 255 - np.abs(scaled.astype(int) - 128) * 2
    b = 255 - scaled
    return np.stack([r, g, b], axis=-1).astype(np.uint8)

def generate_frames():
    while True:
        try:
            frames = pipeline.wait_for_frames(5000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            # RGB Dönüşümü
            raw_bytes = np.asanyarray(color_frame.get_data()).flatten()
            rgb_data = yuyv_to_rgb(raw_bytes, color_frame.get_width(), color_frame.get_height())
            
            # Derinlik Dönüşümü
            depth_data = np.asanyarray(depth_frame.get_data())
            depth_color = depth_to_colormap(depth_data)

            # Mesafe Okuma
            dw, dh = depth_frame.get_width(), depth_frame.get_height()
            dist = depth_frame.get_distance(dw // 2, dh // 2)

            # PIL İle Birleştirme
            img_rgb = Image.fromarray(rgb_data)
            img_depth = Image.fromarray(depth_color)

            # RGB Üzerine Artı Göstergesi ve Mesafe Yazısı
            draw = ImageDraw.Draw(img_rgb)
            cw, ch = img_rgb.size
            draw.ellipse([cw//2-5, ch//2-5, cw//2+5, ch//2+5], fill=(0, 255, 0))
            draw.text((15, 15), f"Merkez Mesafe: {dist:.2f} m", fill=(0, 255, 0))

            # İki Görüntüyü Yan Yana Koy (1280x480 veya 640x240)
            combined = Image.new('RGB', (cw + img_depth.width, max(ch, img_depth.height)))
            combined.paste(img_rgb, (0, 0))
            combined.paste(img_depth, (cw, 0))

            # JPEG Formatında Hazırla
            buf = io.BytesIO()
            combined.save(buf, format='JPEG', quality=70)
            frame_bytes = buf.getvalue()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

        except Exception as e:
            pass

# HTML & CSS Arayüzü (RealSense Viewer Temalı Dark Mode)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Python RealSense Viewer</title>
    <style>
        body { background-color: #1b1b1e; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: #007acc; font-size: 24px; }
        .main-container { display: flex; gap: 20px; }
        .viewport { flex: 3; background-color: #000; border: 1px solid #444; border-radius: 8px; overflow: hidden; text-align: center; }
        .viewport img { width: 100%; max-width: 1280px; height: auto; display: block; }
        .controls { flex: 1; background-color: #252526; padding: 20px; border-radius: 8px; border: 1px solid #3c3c3c; height: fit-content; }
        .controls h3 { color: #007acc; margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 8px; }
        .control-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; font-size: 14px; color: #ccc; }
        input[type=range] { width: 100%; }
        .btn { background-color: #0e639c; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; width: 100%; font-weight: bold; }
        .btn:hover { background-color: #1177bb; }
        .info-card { background-color: #333337; padding: 10px; border-radius: 4px; font-size: 13px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Intel RealSense Python Viewer</h1>
        <span>Sürücü Modu: Native USB / Saf Python</span>
    </div>

    <div class="main-container">
        <div class="viewport">
            <img src="/video_feed" alt="Kamera Akışı">
        </div>

        <div class="controls">
            <h3>Donanım Ayarları</h3>
            
            <div class="control-group">
                <label>Lazer Gücü (Laser Power)</label>
                <input type="range" id="laserPower" min="0" max="360" step="10" value="150" onchange="updateLaser(this.value)">
                <span id="laserVal" style="font-size: 12px; color: #888;">150 mW</span>
            </div>

            <div class="control-group">
                <button class="btn" onclick="toggleOption('emitter')">IR Emitter (Lazer) Aç/Kapat</button>
            </div>

            <div class="control-group">
                <button class="btn" onclick="toggleOption('exposure')">Otomatik Pozlama (Auto Exposure)</button>
            </div>

            <div class="info-card">
                <b>Bilgi:</b><br>
                • Sol taraf: RGB (Renkli) Kamera<br>
                • Sağ taraf: Derinlik (Mesafe) Haritası<br>
                • Yeşil Nokta: Canlı Merkez Ölçümü
            </div>
        </div>
    </div>

    <script>
        function updateLaser(val) {
            document.getElementById('laserVal').innerText = val + " mW";
            fetch('/set_laser?power=' + val);
        }
        function toggleOption(opt) {
            fetch('/toggle_option?opt=' + opt);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_laser')
def set_laser():
    power = float(request.args.get('power', 150))
    if depth_sensor.supports(rs.option.laser_power):
        depth_sensor.set_option(rs.option.laser_power, power)
    return jsonify(status="ok")

@app.route('/toggle_option')
def toggle_option():
    opt = request.args.get('opt')
    if opt == 'emitter' and depth_sensor.supports(rs.option.emitter_enabled):
        curr = depth_sensor.get_option(rs.option.emitter_enabled)
        depth_sensor.set_option(rs.option.emitter_enabled, 0.0 if curr > 0 else 1.0)
    elif opt == 'exposure' and depth_sensor.supports(rs.option.enable_auto_exposure):
        curr = depth_sensor.get_option(rs.option.enable_auto_exposure)
        depth_sensor.set_option(rs.option.enable_auto_exposure, 0.0 if curr > 0 else 1.0)
    return jsonify(status="ok")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
