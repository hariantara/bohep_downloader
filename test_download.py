#!/usr/bin/env python3

from bohep_downloader.downloader import BohepDownloader

def main():
    # Create downloader instance
    downloader = BohepDownloader()
    
    # Get URL from user
    url = input("Enter video URL: ").strip()
    
    # Get quality from user
    quality = input("Enter quality (e.g. 720p, 1080p): ").strip()
    
    # Get save directory (optional)
    save_dir = input("Enter save directory (press Enter for default): ").strip()
    if not save_dir:
        save_dir = None
    
    try:
        # Download the video
        downloader.download(url, quality, save_dir)
        print("Download completed successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 