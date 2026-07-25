import numpy as np
from PIL import Image
import os

INPUT_PATH = "kamera_kayitlari/derinlik_verilari.npz"
OUTPUT_DIR = "kamera_kayitlari/kareler"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print(f"{INPUT_PATH} dosyası yükleniyor...")

# 1. NumPy arşivini yükle
with np.load(INPUT_PATH) as data:
    # Dosya içindeki tüm karelerin anahtarlarını al (arr_0, arr_1 vb.)
    frame_keys = sorted(data.files, key=lambda x: int(x.split('_')[1]))
    total_frames = len(frame_keys)
    print(f"Toplam {total_frames} adet derinlik karesi bulundu.")

    # 2. Her bir kareyi görsele dönüştür
    for idx, key in enumerate(frame_keys):
        depth_matrix = data[key]

        # Ham milimetre verisini gözle görülebilmesi için 0-255 arasına ölçekle
        # Yakın nesneler beyaz/açık gri, uzak nesneler siyah/koyu gri görünür
        max_dist = 4000 # 4 metreye kadar olan alanı ölçekle
        scaled_depth = np.clip(depth_matrix, 0, max_dist)
        normalized = ((scaled_depth / max_dist) * 255).astype(np.uint8)

        # Görseli ters çevirelim: Yakın yerler parlak, uzak yerler karanlık olsun
        visual_matrix = 255 - normalized

        # Pillow ile PNG olarak kaydet
        img = Image.fromarray(visual_matrix)
        output_path = os.path.join(OUTPUT_DIR, f"kare_{idx:04d}.png")
        img.save(output_path)

        print(f"Dönüştürülüyor: {idx+1}/{total_frames}", end="\r")

print(f"\n\n✓ İşlem tamamlandı! Kareler şu klasöre kaydedildi: {OUTPUT_DIR}")
