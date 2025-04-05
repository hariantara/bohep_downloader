#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

def create_dmg():
    # Paths
    workspace = Path(os.getcwd())
    dist_dir = workspace / 'dist'
    app_name = 'Bohep Downloader.app'
    dmg_name = 'Bohep-Downloader.dmg'
    
    # Create a temporary directory for DMG contents
    temp_dir = dist_dir / 'dmg_temp'
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy the app to the temporary directory
    app_source = dist_dir / 'bohep-downloader-darwin-arm64-package' / app_name
    app_dest = temp_dir / app_name
    if app_source.exists():
        shutil.copytree(app_source, app_dest, dirs_exist_ok=True)
        
        # Set proper permissions
        os.system(f'chmod -R 755 "{app_dest}"')
        os.system(f'chmod +x "{app_dest}/Contents/MacOS/"*')
    else:
        print(f"Error: Source app not found at {app_source}")
        return
    
    # Create a symbolic link to Applications folder
    os.symlink('/Applications', temp_dir / 'Applications')
    
    # Create the DMG
    dmg_path = dist_dir / dmg_name
    if dmg_path.exists():
        os.unlink(dmg_path)
    
    # Use create-dmg to create the DMG
    subprocess.run([
        'create-dmg',
        '--volname', 'Bohep Downloader',
        '--window-pos', '200', '120',
        '--window-size', '800', '400',
        '--icon-size', '100',
        '--icon', app_name, '200', '200',
        '--hide-extension', app_name,
        '--app-drop-link', '600', '200',
        str(dmg_path),
        str(temp_dir)
    ], check=True)
    
    # Set proper permissions on the DMG
    os.system(f'chmod 755 "{dmg_path}"')
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    print(f"\nDMG created successfully at:\n{dmg_path}")
    print("\nTo install:")
    print("1. Double-click the DMG file")
    print("2. Drag 'Bohep Downloader' to the Applications folder")
    print("3. Eject the DMG")
    print("4. You can now launch the app from your Applications folder")

if __name__ == '__main__':
    create_dmg() 