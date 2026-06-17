"""
Download required MediaPipe models
"""

import os
import urllib.request
import ssl

# Create models directory
os.makedirs("models", exist_ok=True)

# Disable SSL verification for downloading
ssl._create_default_https_context = ssl._create_unverified_context

# Model URLs
models = {
    "hand_landmarker": [
        "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task",
        "https://github.com/google-ai-edge/mediapipe/releases/download/v0.10.0/hand_landmarker.task",
    ]
}

for name, urls in models.items():
    model_path = os.path.join("models", f"{name}.task")

    # Check if model already exists
    if os.path.exists(model_path):
        try:
            with open(model_path, "rb") as f:
                content = f.read(200)

            # Check if downloaded file is actually an XML error page
            if b"<Error>" in content or b"<?xml" in content:
                print(f"✗ Model '{name}' is corrupted. Re-downloading...")
                os.remove(model_path)
            else:
                print(f"✓ Model '{name}' already exists.")
                continue

        except Exception as e:
            print(f"Error reading existing model: {e}")
            os.remove(model_path)

    downloaded = False

    for url in urls:
        print(f"\nTrying to download '{name}' from:")
        print(url)

        try:
            urllib.request.urlretrieve(url, model_path)

            # Verify downloaded file
            if os.path.getsize(model_path) == 0:
                raise Exception("Downloaded file is empty.")

            with open(model_path, "rb") as f:
                header = f.read(200)

            if b"<Error>" in header or b"<?xml" in header:
                raise Exception("Downloaded XML error page instead of model.")

            print(f"✓ Successfully downloaded '{name}'")
            downloaded = True
            break

        except Exception as e:
            print(f"✗ Failed: {e}")

            if os.path.exists(model_path):
                os.remove(model_path)

    if not downloaded:
        print(f"\n✗ Could not download '{name}' from any source.")

print("\n==============================")
print("Setup Complete!")
print("==============================")