#!/usr/bin/env python3

import os
import sys
import platform
import subprocess
import shutil
from download_dependencies import main as download_dependencies

def build_windows_executable():
    """Build Windows executable using Wine."""
    # Check if Wine is installed
    try:
        subprocess.run(['wine', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Wine is not installed. Please install Wine to build Windows executables.")
        print("On macOS: brew install --cask wine-stable")
        print("On Linux: sudo apt-get install wine")
        sys.exit(1)
    
    # Clean up existing build and dist directories
    for dir_to_clean in ['build', 'dist']:
        if os.path.exists(dir_to_clean):
            shutil.rmtree(dir_to_clean)
    
    # PyInstaller options for Windows
    pyinstaller_options = [
        '--onefile',  # Create a single executable
        '--clean',    # Clean PyInstaller cache
        '--noconfirm',  # Replace existing build without asking
        '--name', 'bohep-downloader-windows-x86_64',  # Windows executable name
        '--add-data', f'bohep_downloader/decode_packed.js{os.pathsep}bohep_downloader',  # Include JS file
        '--icon', 'icon.ico',  # Windows icon
        '--target-architecture', 'x86_64',  # Target 64-bit Windows
        '--hidden-import', 'encodings',  # Ensure encodings module is included
        '--hidden-import', 'encodings.aliases',  # Include encodings aliases
        '--hidden-import', 'encodings.utf_8',  # Include UTF-8 encoding
        '--hidden-import', 'encodings.ascii',  # Include ASCII encoding
        '--hidden-import', 'encodings.latin_1',  # Include Latin-1 encoding
        '--runtime-hook', 'runtime_hook.py',  # Add runtime hook
    ]
    
    # Add the main script
    pyinstaller_options.append('bohep_downloader/cli.py')
    
    # Run PyInstaller through Wine
    subprocess.run(['wine', 'pyinstaller'] + pyinstaller_options)
    
    # Create distribution directory
    dist_dir = 'dist/bohep-downloader-windows-x86_64-package'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy executable to distribution directory
    executable_name = 'bohep-downloader-windows-x86_64.exe'
    executable_path = os.path.join('dist', executable_name)
    if os.path.exists(executable_path):
        shutil.copy(executable_path, os.path.join(dist_dir, executable_name))
    
    # Download Windows dependencies
    download_dependencies()
    
    # Create Windows batch file
    with open(os.path.join(dist_dir, 'run.bat'), 'w', newline='\r\n') as f:
        f.write('@echo off\n')
        f.write('set PATH=%~dp0ffmpeg\\bin;%~dp0nodejs;%PATH%\n')
        f.write(f'"%~dp0{executable_name}" %*\n')
    
    # Create README.txt
    with open(os.path.join(dist_dir, 'README.txt'), 'w', newline='\r\n') as f:
        f.write('Bohep Downloader for Windows\n')
        f.write('==========================\n\n')
        f.write('To use the downloader:\n\n')
        f.write('1. Double-click run.bat\n')
        f.write('2. Enter the video URL when prompted\n')
        f.write('3. Select the desired video quality\n')
        f.write('4. The video will be downloaded to your Downloads folder\n\n')
        f.write('Note: If you get a security warning, right-click run.bat and select "Run as administrator"\n')
    
    # Create ZIP archive
    shutil.make_archive('bohep-downloader-windows-x86_64', 'zip', dist_dir)
    
    print("Windows build completed. Executable is in", dist_dir)
    print("Distribution archive created: bohep-downloader-windows-x86_64.zip")

def build_executable():
    """Build standalone executable for the current platform."""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == 'windows':
        build_windows_executable()
        return
    
    # Clean up existing build and dist directories
    for dir_to_clean in ['build', 'dist']:
        if os.path.exists(dir_to_clean):
            shutil.rmtree(dir_to_clean)
    
    # Common PyInstaller options
    pyinstaller_options = [
        '--onefile',  # Create a single executable
        '--clean',    # Clean PyInstaller cache
        '--noconfirm',  # Replace existing build without asking
        '--name', f'bohep-downloader-{system}-{arch}',  # Name based on platform and architecture
        '--add-data', f'bohep_downloader/decode_packed.js{os.pathsep}bohep_downloader',  # Include JS file
        '--hidden-import', 'bohep_downloader',  # Ensure package is included
        '--hidden-import', 'bohep_downloader.downloader',  # Ensure module is included
        '--hidden-import', 'encodings',  # Ensure encodings module is included
        '--hidden-import', 'encodings.aliases',  # Include encodings aliases
        '--hidden-import', 'encodings.utf_8',  # Include UTF-8 encoding
        '--hidden-import', 'encodings.ascii',  # Include ASCII encoding
        '--hidden-import', 'encodings.latin_1',  # Include Latin-1 encoding
        '--collect-all', 'bohep_downloader',  # Collect all package data
        '--add-data', f'bohep_downloader/decode_packed.js{os.pathsep}.',  # Also include JS file in root
        '--runtime-hook', 'runtime_hook.py',  # Add runtime hook
    ]
    
    # Platform-specific options
    if system == 'darwin':  # macOS
        pyinstaller_options.extend([
            '--icon', 'icon.icns',  # macOS icon
            '--target-architecture', 'arm64' if arch == 'arm64' else 'x86_64',  # Target architecture
        ])
    elif system == 'linux':
        pyinstaller_options.extend([
            '--icon', 'icon.png',  # Linux icon
        ])
    elif system == 'windows':
        pyinstaller_options.extend([
            '--icon', 'icon.ico',  # Windows icon
        ])
    
    # Add the main script
    pyinstaller_options.append('bohep_downloader/cli.py')
    
    # Run PyInstaller
    subprocess.run(['pyinstaller'] + pyinstaller_options)
    
    # Create distribution directory
    dist_dir = f'dist/bohep-downloader-{system}-{arch}-package'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy executable to distribution directory
    executable_name = f'bohep-downloader-{system}-{arch}'
    if system == 'windows':
        executable_name += '.exe'
    
    executable_path = os.path.join('dist', executable_name)
    if os.path.exists(executable_path):
        shutil.copy(executable_path, os.path.join(dist_dir, executable_name))
    
    # Also copy the JS file directly to the distribution directory
    js_file_path = os.path.join('bohep_downloader', 'decode_packed.js')
    if os.path.exists(js_file_path):
        shutil.copy(js_file_path, os.path.join(dist_dir, 'decode_packed.js'))
    
    # Download dependencies
    download_dependencies()
    
    # Create platform-specific launcher scripts
    if system == 'darwin':  # macOS
        # For macOS, create an app bundle
        app_dir = os.path.join(dist_dir, 'Bohep Downloader.app', 'Contents', 'MacOS')
        os.makedirs(app_dir, exist_ok=True)
        
        # Copy executable to app bundle
        if os.path.exists(executable_path):
            shutil.copy(executable_path, os.path.join(app_dir, executable_name))
        
        # Copy JS file to app bundle
        if os.path.exists(js_file_path):
            shutil.copy(js_file_path, os.path.join(app_dir, 'decode_packed.js'))
        
        # Create Info.plist
        with open(os.path.join(dist_dir, 'Bohep Downloader.app', 'Contents', 'Info.plist'), 'w') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher.command</string>
    <key>CFBundleIdentifier</key>
    <string>com.bohep.downloader</string>
    <key>CFBundleName</key>
    <string>Bohep Downloader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>''')
        
        # Create launcher script
        launcher_path = os.path.join(app_dir, 'launcher.command')
        with open(launcher_path, 'w') as f:
            f.write('''#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Open Terminal.app and run the actual script
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR' && clear && echo '===================================================='; echo '           Bohep Downloader - Video Downloader        '; echo '===================================================='; echo ''; echo 'Please paste the video URL below:'; echo 'Example: https://missav.ws/dm65/id/fsdss-753'; echo ''; while true; do echo -n 'URL (or type \\"exit\\" to quit): '; read url; if [ \\"\\$url\\" = \\"exit\\" ]; then break; fi; if [ ! -z \\"\\$url\\" ]; then ./bohep-downloader-darwin-arm64 \\"\\$url\\" || true; fi; echo ''; echo 'Press Enter to continue...'; read; clear; echo '===================================================='; echo '           Bohep Downloader - Video Downloader        '; echo '===================================================='; echo ''; echo 'Please paste the video URL below:'; echo 'Example: https://missav.ws/dm65/id/fsdss-753'; echo ''; done; echo 'Thank you for using Bohep Downloader!'; echo 'Press Enter to exit...'; read"
end tell
EOF''')
        
        # Make launcher script executable
        os.chmod(launcher_path, 0o755)
    
    elif system == 'linux':
        # For Linux, create a shell script to run the executable
        with open(os.path.join(dist_dir, 'run.sh'), 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('export PATH="$PWD/ffmpeg/bin:$PWD/nodejs/bin:$PATH"\n')
            f.write(f'"$PWD/{executable_name}" "$@"\n')
        
        # Make the shell script executable
        os.chmod(os.path.join(dist_dir, 'run.sh'), 0o755)
    
    elif system == 'windows':
        # For Windows, create a batch file to run the executable
        with open(os.path.join(dist_dir, 'run.bat'), 'w', newline='\r\n') as f:
            f.write('@echo off\n')
            f.write('set PATH=%~dp0ffmpeg\\bin;%~dp0nodejs;%PATH%\n')
            f.write(f'"%~dp0{executable_name}" %*\n')
    
    # Create a ZIP archive for distribution
    if system == 'windows':
        shutil.make_archive(f'bohep-downloader-{system}-{arch}', 'zip', dist_dir)
    else:
        shutil.make_archive(f'bohep-downloader-{system}-{arch}', 'tar', dist_dir)
        # Also create a gzipped tar for Linux
        if system == 'linux':
            subprocess.run(['gzip', f'bohep-downloader-{system}-{arch}.tar'])
    
    print(f"Build completed for {system} ({arch}). Executable is in {dist_dir}")
    print(f"Distribution archive created: bohep-downloader-{system}-{arch}.{'zip' if system == 'windows' else 'tar.gz'}")

if __name__ == "__main__":
    # Check if we should build for Windows specifically
    if len(sys.argv) > 1 and sys.argv[1] == '--windows':
        build_windows_executable()
    else:
        build_executable() 