import os
import sys
import urllib.request
import zipfile

TOOLS_DIR = os.path.abspath('_build_tools')
os.makedirs(TOOLS_DIR, exist_ok=True)

def download(url, filename):
    dest = os.path.join(TOOLS_DIR, filename)
    if os.path.exists(dest):
        print(f"[OK] {filename} already exists ({os.path.getsize(dest)} bytes).")
        return dest

    print(f"[...] Downloading {filename} from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        chunk_size = 1024 * 512
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 / total
                sys.stdout.write(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB ({pct:.1f}%)")
            else:
                sys.stdout.write(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB")
            sys.stdout.flush()
    print(f"\n[DONE] Saved {filename}")
    return dest

def main():
    print("=== Downloading Android Build Tools ===")
    # 1. aapt2
    aapt2_jar = download('https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.2.2-10154469/aapt2-8.2.2-10154469-windows.jar', 'aapt2.jar')
    aapt2_exe = os.path.join(TOOLS_DIR, 'aapt2.exe')
    if not os.path.exists(aapt2_exe):
        print("Extracting aapt2.exe...")
        with zipfile.ZipFile(aapt2_jar, 'r') as z:
            with z.open('aapt2.exe') as src, open(aapt2_exe, 'wb') as dst:
                dst.write(src.read())
        print("[OK] aapt2.exe extracted.")

    # 2. android.jar
    download('https://raw.githubusercontent.com/Sable/android-platforms/master/android-30/android.jar', 'android.jar')

    # 3. r8 (d8)
    download('https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.2.33/r8-8.2.33.jar', 'r8.jar')

    # 4. uber-apk-signer
    download('https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar', 'uber-apk-signer.jar')

    # 5. OpenJDK 17
    jdk_zip = download('https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.14%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.14_7.zip', 'jdk17.zip')
    jdk_dir = os.path.join(TOOLS_DIR, 'jdk')
    if not os.path.exists(jdk_dir):
        print("Extracting OpenJDK 17...")
        with zipfile.ZipFile(jdk_zip, 'r') as z:
            z.extractall(TOOLS_DIR)
        # Find extracted folder and rename to jdk
        for item in os.listdir(TOOLS_DIR):
            if item.startswith('jdk-17') and os.path.isdir(os.path.join(TOOLS_DIR, item)):
                os.rename(os.path.join(TOOLS_DIR, item), jdk_dir)
                break
        print("[OK] OpenJDK 17 extracted.")

    print("\nAll tools ready!")

if __name__ == '__main__':
    main()
