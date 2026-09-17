import os
import sys
import subprocess
import glob
import zipfile
import shutil

# Force UTF-8 on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DRIVE = "Y:"

# Ensure Y: drive mapping exists
if not os.path.exists(f"{DRIVE}\\"):
    cwd = os.path.abspath(os.path.dirname(__file__))
    subprocess.run(['subst', DRIVE, cwd], check=True)

BASE_DIR = f"{DRIVE}\\"
TOOLS_DIR = os.path.join(BASE_DIR, '_build_tools')
BUILD_DIR = os.path.join(BASE_DIR, 'build')

AAPT2 = os.path.join(TOOLS_DIR, 'aapt2.exe')
ANDROID_JAR = os.path.join(TOOLS_DIR, 'android.jar')
R8_JAR = os.path.join(TOOLS_DIR, 'r8.jar')
SIGNER_JAR = os.path.join(TOOLS_DIR, 'uber-apk-signer.jar')
JDK_BIN = os.path.join(TOOLS_DIR, 'jdk', 'bin')
JAVAC = os.path.join(JDK_BIN, 'javac.exe')
JAVA = os.path.join(JDK_BIN, 'java.exe')

def run(cmd, desc):
    print(f"\n[+] {desc}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] ERROR during {desc}:")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        sys.exit(1)
    return res.stdout

def main():
    print("==================================================")
    print("BUILDING ANDROID 14 COMPLIANT APK: YUME NOTE")
    print("==================================================")

    # 1. Clean build directory
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    compiled_res = os.path.join(BUILD_DIR, 'compiled_res.zip')
    gen_dir = os.path.join(BUILD_DIR, 'gen')
    classes_dir = os.path.join(BUILD_DIR, 'classes')
    dex_dir = os.path.join(BUILD_DIR, 'dex')
    unaligned_apk = os.path.join(BUILD_DIR, 'unaligned.apk')
    final_apk = os.path.join(BASE_DIR, 'YumeNote.apk')

    os.makedirs(gen_dir, exist_ok=True)
    os.makedirs(classes_dir, exist_ok=True)
    os.makedirs(dex_dir, exist_ok=True)

    res_dir = os.path.join(BASE_DIR, 'android', 'app', 'src', 'main', 'res')
    manifest = os.path.join(BASE_DIR, 'android', 'app', 'src', 'main', 'AndroidManifest.xml')
    assets_dir = os.path.join(BASE_DIR, 'android', 'app', 'src', 'main', 'assets')

    # Step 1: aapt2 compile resources
    run([AAPT2, 'compile', '--dir', res_dir, '-o', compiled_res], "1. Compiling UI resources (aapt2 compile)")

    # Step 2: aapt2 link with explicit Android 14 targetSdkVersion=34
    run([
        AAPT2, 'link',
        '-o', unaligned_apk,
        '-I', ANDROID_JAR,
        '--manifest', manifest,
        '--min-sdk-version', '24',
        '--target-sdk-version', '34',
        '--version-code', '1',
        '--version-name', '1.0.0',
        '--java', gen_dir,
        '-A', assets_dir,
        '--auto-add-overlay',
        compiled_res
    ], "2. Linking APK & bundling assets for Android 14 (aapt2 link)")

    # Step 3: Compile Java
    java_files = glob.glob(os.path.join(gen_dir, '**', '*.java'), recursive=True)
    main_activity = os.path.join(BASE_DIR, 'android', 'app', 'src', 'main', 'java', 'com', 'yumenote', 'app', 'MainActivity.java')
    java_files.append(main_activity)

    javac_cmd = [JAVAC, '-source', '8', '-target', '8', '-cp', ANDROID_JAR, '-d', classes_dir] + java_files
    run(javac_cmd, "3. Compiling Java sources (javac)")

    # Step 4: Convert .class to classes.dex using D8
    class_files = glob.glob(os.path.join(classes_dir, '**', '*.class'), recursive=True)
    d8_cmd = [JAVA, '-cp', R8_JAR, 'com.android.tools.r8.D8', '--min-api', '24', '--lib', ANDROID_JAR, '--output', dex_dir] + class_files
    run(d8_cmd, "4. Converting bytecode for Android 14 (D8 -> classes.dex)")

    # Step 5: Add classes.dex into unaligned.apk
    print("\n[+] 5. Injecting classes.dex into APK...")
    dex_file = os.path.join(dex_dir, 'classes.dex')
    with zipfile.ZipFile(unaligned_apk, 'a', compression=zipfile.ZIP_DEFLATED) as apk_zip:
        apk_zip.write(dex_file, 'classes.dex')
    print("[OK] classes.dex added to APK.")

    # Step 6: Sign APK with uber-apk-signer (V1, V2, V3 signatures)
    run([
        JAVA, '-jar', SIGNER_JAR,
        '--apks', unaligned_apk,
        '--out', BUILD_DIR,
        '--allowResign'
    ], "6. Digitally signing APK with V1, V2, V3 schemes (uber-apk-signer)")

    # Step 7: Find signed APK and copy to root
    signed_candidates = glob.glob(os.path.join(BUILD_DIR, '*aligned-debugSigned.apk'))
    if not signed_candidates:
        signed_candidates = glob.glob(os.path.join(BUILD_DIR, '*signed*.apk'))

    if signed_candidates:
        shutil.copyfile(signed_candidates[0], final_apk)
        size_mb = os.path.getsize(final_apk) / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"SUCCESS! Android 14 verified APK built:")
        print(f"   File: {final_apk}")
        print(f"   Size: {size_mb:.2f} MB")
        print("   Target SDK: 34 (Android 14)")
        print("   Min SDK: 24 (Android 7.0)")
        print("   Ready for installation on Android 14!")
        print("=" * 60)
    else:
        print("[-] Signed APK not found.")

if __name__ == '__main__':
    main()
