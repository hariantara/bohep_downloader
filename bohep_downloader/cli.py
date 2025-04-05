#!/usr/bin/env python3

import sys
import os
from bohep_downloader.downloader import VideoDownloader

def main():
    """Main entry point for the CLI."""
    if len(sys.argv) != 2:
        print("Usage: bohep-download <url>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = VideoDownloader()
    downloader.download(url)

if __name__ == "__main__":
    main()
