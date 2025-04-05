# Bohep Downloader

A Python-based video downloader application with a modern GUI interface.

## Features

- Modern and user-friendly GUI interface
- Video quality selection
- Download progress tracking
- Custom save location
- Cancel download functionality

## Download

[![Download Bohep Downloader](https://img.shields.io/badge/Download-Bohep%20Downloader-blue.svg)](https://github.com/hariantara/bohep_downloader/releases/latest/download/Bohep%20Downloader.dmg)

## Prerequisites

Before installing Bohep Downloader, make sure you have the following installed:

### macOS
1. Install Homebrew (if not already installed):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install Python and FFmpeg:
```bash
brew install python ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk ffmpeg
```

### Windows
1. Download and install Python from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
2. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract the downloaded zip file
   - Add the `bin` folder to your system's PATH environment variable

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hariantara/bohep_downloader.git
cd bohep_downloader
```

2. Create and activate a virtual environment:

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### macOS/Linux
```bash
python -m bohep_downloader
```

### Windows
```bash
python -m bohep_downloader
```

## Usage

1. Enter the video URL in the input field
2. Click "Check URL" to verify and get available qualities
3. Select desired video quality from the dropdown menu
4. Choose save location (optional)
5. Click "Download" to start downloading
6. Monitor progress in the progress bar
7. Use "Cancel" button to stop the download if needed

## Troubleshooting

### Common Issues

#### FFmpeg Not Found
- **macOS**: Run `brew install ffmpeg`
- **Linux**: Run `sudo apt install ffmpeg`
- **Windows**: Make sure FFmpeg is in your PATH environment variable

#### Python/Tkinter Issues
- **macOS**: Run `brew install python-tk`
- **Linux**: Run `sudo apt install python3-tk`
- **Windows**: Reinstall Python and check "tcl/tk and IDLE" during installation

#### Virtual Environment Issues
If you get permission errors:
- **macOS/Linux**: Use `sudo` before commands or check directory permissions
- **Windows**: Run Command Prompt as Administrator

### Getting Help

If you encounter any issues:
1. Check if all prerequisites are installed correctly
2. Verify that your virtual environment is activated
3. Ensure all dependencies are installed
4. Check the console for error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details. 