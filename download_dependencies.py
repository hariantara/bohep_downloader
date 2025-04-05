#!/usr/bin/env python3

import os
import sys
import platform
import subprocess
import shutil
import requests
import zipfile
import tarfile
import tempfile

def download_file(url, destination):
    """Download a file from a URL to a destination."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def extract_archive(archive_path, extract_path):
    """Extract a ZIP or TAR archive to a destination."""
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_path)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

def download_ffmpeg(system, arch, output_dir):
    """Download FFmpeg binaries for the specified platform."""
    print(f"Downloading FFmpeg for {system} ({arch})...")
    
    if system == 'windows':
        # Windows
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        archive_path = os.path.join(tempfile.gettempdir(), "ffmpeg.zip")
        download_file(url, archive_path)
        
        extract_path = os.path.join(tempfile.gettempdir(), "ffmpeg_extract")
        os.makedirs(extract_path, exist_ok=True)
        extract_archive(archive_path, extract_path)
        
        # Find the extracted directory
        extracted_dir = None
        for item in os.listdir(extract_path):
            if item.startswith("ffmpeg-"):
                extracted_dir = os.path.join(extract_path, item)
                break
        
        if extracted_dir:
            # Copy the bin directory
            ffmpeg_bin_dir = os.path.join(output_dir, "ffmpeg", "bin")
            os.makedirs(ffmpeg_bin_dir, exist_ok=True)
            
            for file in os.listdir(os.path.join(extracted_dir, "bin")):
                shutil.copy(
                    os.path.join(extracted_dir, "bin", file),
                    os.path.join(ffmpeg_bin_dir, file)
                )
        
        # Clean up
        os.remove(archive_path)
        shutil.rmtree(extract_path)
    
    elif system == 'darwin':  # macOS
        # macOS
        if arch == 'arm64':  # Apple Silicon
            url = "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip"
        else:  # Intel
            url = "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip"
        
        archive_path = os.path.join(tempfile.gettempdir(), "ffmpeg.zip")
        download_file(url, archive_path)
        
        # Create the output directory
        ffmpeg_bin_dir = os.path.join(output_dir, "ffmpeg", "bin")
        os.makedirs(ffmpeg_bin_dir, exist_ok=True)
        
        # Extract the binary
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extract("ffmpeg", ffmpeg_bin_dir)
        
        # Make it executable
        os.chmod(os.path.join(ffmpeg_bin_dir, "ffmpeg"), 0o755)
        
        # Clean up
        os.remove(archive_path)
    
    elif system == 'linux':
        # Linux
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = os.path.join(tempfile.gettempdir(), "ffmpeg.tar.xz")
        download_file(url, archive_path)
        
        extract_path = os.path.join(tempfile.gettempdir(), "ffmpeg_extract")
        os.makedirs(extract_path, exist_ok=True)
        
        # Extract using tar
        subprocess.run(['tar', '-xf', archive_path, '-C', extract_path])
        
        # Find the extracted directory
        extracted_dir = None
        for item in os.listdir(extract_path):
            if item.startswith("ffmpeg-"):
                extracted_dir = os.path.join(extract_path, item)
                break
        
        if extracted_dir:
            # Copy the binary
            ffmpeg_bin_dir = os.path.join(output_dir, "ffmpeg", "bin")
            os.makedirs(ffmpeg_bin_dir, exist_ok=True)
            
            shutil.copy(
                os.path.join(extracted_dir, "ffmpeg"),
                os.path.join(ffmpeg_bin_dir, "ffmpeg")
            )
            
            # Make it executable
            os.chmod(os.path.join(ffmpeg_bin_dir, "ffmpeg"), 0o755)
        
        # Clean up
        os.remove(archive_path)
        shutil.rmtree(extract_path)

def download_nodejs(system, arch, output_dir):
    """Download Node.js binaries for the specified platform."""
    print(f"Downloading Node.js for {system} ({arch})...")
    
    if system == 'windows':
        # Windows
        url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
        archive_path = os.path.join(tempfile.gettempdir(), "nodejs.zip")
        download_file(url, archive_path)
        
        # Create the output directory
        nodejs_dir = os.path.join(output_dir, "nodejs")
        os.makedirs(nodejs_dir, exist_ok=True)
        
        # Extract the archive
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(nodejs_dir)
        
        # Clean up
        os.remove(archive_path)
    
    elif system == 'darwin':  # macOS
        # macOS
        if arch == 'arm64':  # Apple Silicon
            url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-darwin-arm64.tar.gz"
        else:  # Intel
            url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-darwin-x64.tar.gz"
        
        archive_path = os.path.join(tempfile.gettempdir(), "nodejs.tar.gz")
        download_file(url, archive_path)
        
        # Create the output directory
        nodejs_dir = os.path.join(output_dir, "nodejs")
        os.makedirs(nodejs_dir, exist_ok=True)
        
        # Extract the archive
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(nodejs_dir)
        
        # Clean up
        os.remove(archive_path)
    
    elif system == 'linux':
        # Linux
        url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-linux-x64.tar.xz"
        archive_path = os.path.join(tempfile.gettempdir(), "nodejs.tar.xz")
        download_file(url, archive_path)
        
        # Create the output directory
        nodejs_dir = os.path.join(output_dir, "nodejs")
        os.makedirs(nodejs_dir, exist_ok=True)
        
        # Extract the archive
        subprocess.run(['tar', '-xf', archive_path, '-C', nodejs_dir])
        
        # Clean up
        os.remove(archive_path)

def main():
    """Download FFmpeg and Node.js binaries for the current platform."""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # Map architecture names
    if arch == 'x86_64':
        arch = 'x64'
    elif arch == 'aarch64':
        arch = 'arm64'
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", f"bohep-downloader-{system}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Download dependencies
    download_ffmpeg(system, arch, output_dir)
    download_nodejs(system, arch, output_dir)
    
    print(f"Dependencies downloaded to {output_dir}")

if __name__ == "__main__":
    main() 