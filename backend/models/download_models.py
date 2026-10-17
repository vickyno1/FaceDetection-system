"""
Model Downloader for OpenCV YuNet and SFace ONNX models.

Downloads official pretrained models from OpenCV Zoo GitHub repository:
- YuNet: Lightweight, high-performance face detector (2023mar release)
- SFace: High-accuracy face feature extractor and recognizer (2021dec release)
"""

import os
import sys
import hashlib
import urllib.request

MODELS = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "expected_sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "description": "YuNet Face Detector (ONNX)",
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "expected_sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "description": "SFace Face Recognition Model (ONNX)",
    },
}

def verify_file(filepath: str, expected_sha256: str = None) -> bool:
    if not os.path.exists(filepath):
        return False
    size = os.path.getsize(filepath)
    # LFS pointer files are typically < 500 bytes
    if size < 1000:
        return False
    if expected_sha256:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().lower() == expected_sha256.lower()
    return True

def download_models(target_dir: str = None):
    if target_dir is None:
        target_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(target_dir, exist_ok=True)
    print(f"Target model directory: {target_dir}")

    for filename, info in MODELS.items():
        destination = os.path.join(target_dir, filename)
        if verify_file(destination, info["expected_sha256"]):
            size_mb = os.path.getsize(destination) / (1024 * 1024)
            print(f"[OK] {filename} already exists and is valid ({size_mb:.2f} MB). Skipping.")
            continue

        url = info["url"]
        desc = info["description"]
        print(f"\nDownloading {desc} from {url}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "StudentAttendanceSystem/1.0 (Python/OpenCV)"}
            )
            with urllib.request.urlopen(req) as response, open(destination, "wb") as out_file:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.2f}/{total_size / (1024*1024):.2f} MB)", end="", flush=True)
                    else:
                        print(f"\rDownloaded {downloaded / (1024*1024):.2f} MB...", end="", flush=True)
            print()

            if verify_file(destination, info["expected_sha256"]):
                print(f"[SUCCESS] Downloaded and verified {filename}.")
            else:
                print(f"[WARNING] Downloaded {filename}, but verification check flagged potential size/checksum mismatch.")
        except Exception as e:
            print(f"[ERROR] Failed to download {filename}: {e}")
            if os.path.exists(destination):
                os.remove(destination)
            raise

if __name__ == "__main__":
    download_models()
