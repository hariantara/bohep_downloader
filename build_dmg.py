#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from pathlib import Path

def sign_app():
    """Sign the app bundle with Developer ID certificate."""
    print("Signing app bundle...")
    app_path = Path("dist/Bohep Downloader.app")
    
    # First, sign the JavaScript file
    js_path = app_path / "Contents/MacOS/decode_packed.js"
    if js_path.exists():
        print("Signing JavaScript file...")
        cmd = [
            "codesign",
            "--force",
            "--sign", "Developer ID Application: Jet Chay (B27HBST3DP)",
            "--timestamp",
            str(js_path)
        ]
        subprocess.run(cmd, check=True)
    
    # Sign the Python framework
    python_framework = app_path / "Contents/Frameworks/Python.framework"
    if python_framework.exists():
        print("Signing Python framework...")
        cmd = [
            "codesign",
            "--force",
            "--sign", "Developer ID Application: Jet Chay (B27HBST3DP)",
            "--timestamp",
            "--deep",
            str(python_framework)
        ]
        subprocess.run(cmd, check=True)
    
    # Then sign the entire app bundle
    print("Signing app bundle...")
    cmd = [
        "codesign",
        "--force",
        "--options", "runtime",
        "--sign", "Developer ID Application: Jet Chay (B27HBST3DP)",
        "--timestamp",
        "--deep",
        "--verbose",
        str(app_path)
    ]
    
    subprocess.run(cmd, check=True)
    print("App bundle signed successfully")

def create_app_bundle():
    """Create the app bundle using PyInstaller."""
    print("Creating app bundle...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Check if FFmpeg is installed
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        print("Installing FFmpeg...")
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
    
    # Get FFmpeg path
    ffmpeg_path = subprocess.check_output(["which", "ffmpeg"]).decode().strip()
    
    # PyInstaller command with proper macOS app bundle settings
    cmd = [
        "pyinstaller",
        "--name=Bohep Downloader",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--debug=all",  # Enable debug mode
        "--icon=assets/icon.icns",
        "--add-data=assets:assets",
        "--add-data=bohep_downloader/decode_packed.js:Resources",  # Add decode_packed.js to Resources
        "--add-data=bohep_downloader/decode_packed.js:MacOS",  # Add decode_packed.js to MacOS
        f"--add-binary={ffmpeg_path}:MacOS",  # Add FFmpeg binary
        "--target-arch=arm64",  # For Apple Silicon
        "--collect-all=customtkinter",  # Ensure customtkinter is fully bundled
        "--collect-all=tkinter",  # Ensure tkinter is fully bundled
        "--collect-all=PIL",  # Ensure PIL/Pillow is fully bundled
        "--collect-all=yt_dlp",  # Ensure yt-dlp is fully bundled
        "bohep_downloader/__main__.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    # Set proper permissions
    app_path = Path("dist/Bohep Downloader.app")
    if not app_path.exists():
        raise Exception("App bundle creation failed")
    
    # Set executable permissions
    os.system(f'chmod -R 755 "{app_path}"')
    os.system(f'chmod +x "{app_path}/Contents/MacOS/"*')
    
    # Copy decode_packed.js to multiple locations to ensure it's found
    resources_path = app_path / "Contents/Resources"
    macos_path = app_path / "Contents/MacOS"
    
    # Copy to Resources directory
    shutil.copy("bohep_downloader/decode_packed.js", resources_path / "decode_packed.js")
    
    # Copy to MacOS directory
    shutil.copy("bohep_downloader/decode_packed.js", macos_path / "decode_packed.js")
    
    # Create Info.plist if it doesn't exist
    info_plist = app_path / "Contents/Info.plist"
    if not info_plist.exists():
        with open(info_plist, "w") as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Bohep Downloader</string>
    <key>CFBundleExecutable</key>
    <string>Bohep Downloader</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.bohep.downloader</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Bohep Downloader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSEnvironment</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>@executable_path/../Resources/lib/python3.13/site-packages</string>
        <key>NODE_PATH</key>
        <string>@executable_path/../Resources</string>
        <key>PATH</key>
        <string>@executable_path/../MacOS:@executable_path/../Resources</string>
    </dict>
</dict>
</plist>''')

def create_dmg():
    """Create a DMG file from the app bundle."""
    print("Creating DMG file...")
    
    # DMG settings
    volume_name = "Bohep Downloader"
    dmg_name = "Bohep Downloader.dmg"
    app_path = Path("dist/Bohep Downloader.app")
    dmg_path = Path(f"dist/{dmg_name}")
    
    # Remove existing DMG if it exists
    if dmg_path.exists():
        dmg_path.unlink()
    
    # Create DMG
    cmd = [
        "create-dmg",
        "--volname", volume_name,
        "--volicon", "assets/icon.icns",
        "--window-pos", "200", "120",
        "--window-size", "800", "400",
        "--icon-size", "100",
        "--icon", f"{volume_name}.app", "190", "190",
        "--hide-extension", f"{volume_name}.app",
        "--app-drop-link", "600", "185",
        str(dmg_path),
        str(app_path)
    ]
    
    subprocess.run(cmd, check=True)
    print(f"DMG created successfully at: {dmg_path}")

def main():
    """Main build process."""
    try:
        # Check if create-dmg is installed
        if subprocess.run(["which", "create-dmg"], capture_output=True).returncode != 0:
            print("Installing create-dmg...")
            subprocess.run(["brew", "install", "create-dmg"], check=True)
        
        # Create app bundle
        create_app_bundle()
        
        # Sign the app bundle
        sign_app()
        
        # Create DMG
        create_dmg()
        
        print("\nBuild completed successfully!")
        print("You can find the DMG file in the dist directory.")
        
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 