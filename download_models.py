#!/usr/bin/env python3
"""
Model Downloader for LiteVTT
Downloads Whisper models from Hugging Face (ggerganov/whisper.cpp).
"""

import os
import sys
import ssl
import urllib.request
import certifi
from tqdm import tqdm

MODELS = {
    "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    "small.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
}

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    # Use certifi certificates — required on fresh macOS Python installs
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
    urllib.request.install_opener(opener)

    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

def main():
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("LiteVTT Model Downloader")
    print("========================")
    print("1. Base Model (~140MB) - Faster, good for standard dictation")
    print("2. Small English Model (~460MB) - Slower, much higher accuracy")
    print("3. Both")
    
    choice = input("\nSelect models to download (1-3): ").strip()
    
    to_download = []
    if choice == "1":
        to_download.append("base")
    elif choice == "2":
        to_download.append("small.en")
    elif choice == "3":
        to_download.extend(["base", "small.en"])
    else:
        print("Invalid choice. Exiting.")
        return

    for model_key in to_download:
        url = MODELS[model_key]
        filename = os.path.basename(url)
        output_path = os.path.join(models_dir, filename)
        
        if os.path.exists(output_path):
            print(f"\n{filename} already exists. Skipping.")
            continue
            
        print(f"\nDownloading {filename}...")
        try:
            download_url(url, output_path)
            print(f"✅ Downloaded {filename}")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

if __name__ == "__main__":
    main()
