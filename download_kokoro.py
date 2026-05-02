import urllib.request
import os

files = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}

for filename, url in files.items():
    if os.path.exists(filename):
        print(f"{filename} вже є, пропускаємо")
        continue
    print(f"Качаємо {filename}...")
    urllib.request.urlretrieve(url, filename, 
        reporthook=lambda b, bs, t: print(f"\r  {b*bs/1024/1024:.1f} / {t/1024/1024:.1f} MB", end=""))
    print(f"\n  Готово!")

print("Все скачано!")