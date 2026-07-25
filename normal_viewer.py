from flask import Flask, Response, render_template_string
import cv2
import time

app = Flask(__name__)

# RealSense RGB Sensörüne doğrudan Linux video aygıtı olarak bağlanıyoruz
# 0, 2 veya 4 olabilir. Genelde renkli kamera 0 veya 2'dir.
CAMERA_INDEX = 2  

def get_working_camera():
    for idx in [2, 0, 4, 1, 3]:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            # YUYV formatı ayarla
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✓ Başarıyla RGB Kamera bulundu! Port: /dev/video{idx}")
                return cap
            cap.release()
    return None

cap = get_working_camera()

def generate_frames():
    global cap
    while True:
        if cap is None or not cap.isOpened():
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        # Eğer görüntü pembe/mora kayarsa BGR -> RGB düzeltmesi
        # Doğrudan standart web kamerasının doğal renklerini üretir
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Model Eğitimi Gerçek RGB Kamera</title>
    <style>
        body { background-color: #121212; color: #fff; font-family: sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #0288d1; }
        .viewport { background: #000; border: 2px solid #333; border-radius: 8px; display: inline-block; overflow: hidden; margin-top: 15px; }
        .viewport img { width: 640px; height: 480px; display: block; }
    </style>
</head>
<body>
    <h1>Gerçek Renkli (RGB) Kamera Akışı</h1>
    <p>Model Eğitimi İçin Doğal İnsan ve Ortam Fotoğrafı</p>
    <div class="viewport">
        <img src="/video_feed">
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)