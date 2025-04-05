#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_app_bundle():
    """Create the app bundle using PyInstaller."""
    print("Creating app bundle...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
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
        
        # Create DMG
        create_dmg()
        
        print("\nBuild completed successfully!")
        print("You can find the DMG file in the dist directory.")
        
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 