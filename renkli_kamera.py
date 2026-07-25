import pyrealsense2 as rs
import numpy as np
from PIL import Image, ImageDraw
import time
import os

OUTPUT_DIR = "kamera_kayitlari"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

pipeline = rs.pipeline()
config = rs.config()

# Kameranın YUYV ve Z16 akışlarını talep ediyoruz
config.enable_stream(rs.stream.color, 640, 480, rs.format.yuyv, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

print("Kamera başlatılıyor (Saf YUYV Renkli + Derinlik Modu)...")
profile = pipeline.start(config)

device = profile.get_device()
depth_sensor = device.first_depth_sensor()
if depth_sensor.supports(rs.option.frames_queue_sIze):
    depth_sensor.set_option(rs.option.frames_queue_sIze, 32)

print("\n>>> 5 SANİYELİK GERÇEK RENKLİ KAYIT BAŞLADI <<<")
start_time = time.time()

color_images = []

# %100 DİNAMİK YUYV -> RGB DÖNÜŞTÜRÜCÜ
def yuyv_to_rgb_safe(raw_bytes, actual_w, actual_h):
    total_bytes = len(raw_bytes)

    # Bayt sayısına göre gerçek yüksekliği ve genişliği hesapla
    # YUYV formatında piksel başına 2 bayt düşer (Width * Height * 2 = Total Bytes)
    calc_width = actual_w if actual_w > 0 else 640
    calc_height = total_bytes // (calc_width * 2)

    if calc_height == 0:
        calc_height = actual_h if actual_h > 0 else 480
        calc_width = total_bytes // (calc_height * 2)

    # 2 Piksel = 4 Bayt (Y0, U, Y1, V) -> (Height, Width // 2, 4)
    yuyv = raw_bytes.reshape((calc_height, calc_width // 2, 4))

    Y0 = yuyv[:, :, 0].astype(np.float32)
    U  = yuyv[:, :, 1].astype(np.float32) - 128.0
    Y1 = yuyv[:, :, 2].astype(np.float32)
    V  = yuyv[:, :, 3].astype(np.float32) - 128.0

    R0 = np.clip(Y0 + 1.402 * V, 0, 255)
    G0 = np.clip(Y0 - 0.344136 * U - 0.714136 * V, 0, 255)
    B0 = np.clip(Y0 + 1.772 * U, 0, 255)

    R1 = np.clip(Y1 + 1.402 * V, 0, 255)
    G1 = np.clip(Y1 - 0.344136 * U - 0.714136 * V, 0, 255)
    B1 = np.clip(Y1 + 1.772 * U, 0, 255)

    rgb = np.zeros((calc_height, calc_width, 3), dtype=np.uint8)

    rgb[:, 0::2, 0] = R0.astype(np.uint8)
    rgb[:, 0::2, 1] = G0.astype(np.uint8)
    rgb[:, 0::2, 2] = B0.astype(np.uint8)

    rgb[:, 1::2, 0] = R1.astype(np.uint8)
    rgb[:, 1::2, 1] = G1.astype(np.uint8)
    rgb[:, 1::2, 2] = B1.astype(np.uint8)

    return rgb

try:
    frame_count = 0
    while (time.time() - start_time) < 5:
        frames = pipeline.wait_for_frames(5000)
        
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        raw_bytes = np.asanyarray(color_frame.get_data()).flatten()
        cw = color_frame.get_width()
        ch = color_frame.get_height()

        # Saf Python RGB Dönüşümü
        rgb_data = yuyv_to_rgb_safe(raw_bytes, cw, ch)

        # Derinlik mesafesi
        dw, dh = depth_frame.get_width(), depth_frame.get_height()
        dist = depth_frame.get_distance(dw // 2, dh // 2)

        img_color = Image.fromarray(rgb_data)

        # Görsel üzerine yeşil nokta ve mesafe bilgisi bas
        draw = ImageDraw.Draw(img_color)
        w_img, h_img = img_color.size
        draw.ellipse([w_img // 2 - 4, h_img // 2 - 4, w_img // 2 + 4, h_img // 2 + 4], fill=(0, 255, 0))
        draw.text((10, 10), f"Mesafe: {dist:.2f} m", fill=(0, 255, 0))

        color_images.append(img_color)

        frame_count += 1
        print(f"Kare alındı: {frame_count:03d} | Mesafe: {dist:.2f}m", end="\r")

    print("\n\nKayıt tamamlandı, renkli GIF hazırlanıyor...")
    
    gif_path = os.path.join(OUTPUT_DIR, "renkli_saf_kayit.gif")
    if color_images:
        color_images[0].save(
            gif_path,
            save_all=True,
            append_images=color_images[1:],
            duration=33,
            loop=0
        )
        print(f"\n✓ GERÇEK RENKLİ KAYIT BAŞARIYLA SAKLANDI: {gif_path}")

finally:
    pipeline.stop()
    print("Kamera kapatıldı.")