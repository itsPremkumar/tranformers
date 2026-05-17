import os
import urllib.request
import zipfile

def download_vosk_model():
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    model_dir = "models"
    model_zip = os.path.join(model_dir, "vosk-model-small-en-us.zip")
    extract_path = os.path.join(model_dir, "vosk-model-small-en-us-0.15")

    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    if os.path.exists(extract_path):
        print(f"[VOSK] Model already exists at {extract_path}")
        return extract_path

    print(f"[VOSK] Downloading Wake-Word model... ({model_url})")
    urllib.request.urlretrieve(model_url, model_zip)

    print("[VOSK] Extracting model...")
    with zipfile.ZipFile(model_zip, 'r') as zip_ref:
        zip_ref.extractall(model_dir)
    
    os.remove(model_zip)
    print("[VOSK] Model download complete.")
    return extract_path

if __name__ == "__main__":
    download_vosk_model()
