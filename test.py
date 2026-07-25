import pyrealsense2 as rs
import numpy as np
import time
import os

OUTPUT_DIR = "kamera_kayitlari"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

print("Kamera başlatılıyor...")
profile = pipeline.start(config)

# 1. TAMPON BELLEK BOYUTUNU ARTTIR (Donmayı ve kare tekrarını önler)
device = profile.get_device()
depth_sensor = device.first_depth_sensor()
if depth_sensor.supports(rs.option.frames_queue_sIze):
    depth_sensor.set_option(rs.option.frames_queue_sIze, 32)

RECORD_DURATION = 5  # 5 saniye
print(f"\n>>> {RECORD_DURATION} SANİYELİK KESİNTİSİZ KAYIT BAŞLADI <<<")
print("Lütfen kameranın önünde elinizi/bir nesneyi sürekli hareket ettirin!\n")

start_time = time.time()
depth_frames_list = []

last_matrix = None
repeat_count = 0

DurationTime = 10000

try:
    frame_count = 0
    while (time.time() - start_time) < RECORD_DURATION:
        # Kareyi bekle (Timeout süresi 5000ms)
        frames = pipeline.wait_for_frames(DurationTime)
        depth_frame = frames.get_depth_frame()

        if not depth_frame:
            continue

        # Matris verisini kopyala (.copy() bellek kilitlenmesini çözer)
        depth_data = np.asanyarray(depth_frame.get_data()).copy()

        # Kare gerçekten değişti mi kontrolü (Aynı kare tekrar ediyorsa tespit et)
        if last_matrix is not None:
            if np.array_equal(depth_data, last_matrix):
                repeat_count += 1
            else:
                repeat_count = 0
        last_matrix = depth_data

        depth_frames_list.append(depth_data)
        frame_count += 1

        elapsed = time.time() - start_time
        print(f"Kare: {frame_count:03d} | Geçen Süre: {elapsed:.1f}s | Tekrar Uyarısı: {repeat_count}", end="\r")

    print("\n\nKayıt tamamlandı!")
    print(f"Toplam alınan canlı kare sayısı: {len(depth_frames_list)}")

    # NPZ Olarak Kaydet
    depth_path = os.path.join(OUTPUT_DIR, "derinlik_verilari.npz")
    np.savez_compressed(depth_path, *depth_frames_list)
    print(f"✓ Başarıyla kaydedildi: {depth_path}")

finally:
    pipeline.stop()
    print("Kamera kapatıldı.")