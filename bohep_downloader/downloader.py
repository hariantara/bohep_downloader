#!/usr/bin/env python3

import os
import re
import sys
import json
import requests
import m3u8
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import ffmpeg
import tempfile
import subprocess
import base64
import shlex
import concurrent.futures
import threading
from queue import Queue
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable
import time

class BohepDownloader:
    def __init__(self):
        self.download_dir = str(Path.home() / "Downloads")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Origin': 'https://missav.ws',
            'Referer': 'https://missav.ws/',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Range': 'bytes=0-'
        })
        self.temp_dir = None
        self.output_file = None
        self.progress_callback = None
        self.cancelled = False

    def cancel(self):
        """Cancel the current download operation."""
        self.cancelled = True
        print("Download cancelled by user")
        
    def reset_cancellation(self):
        """Reset the cancellation flag."""
        self.cancelled = False

    def extract_video_id(self, url):
        """Extract video ID from the URL."""
        # Try different URL patterns
        patterns = [
            r'/id/([^/]+)$',  # Standard format
            r'/en/([^/]+)$',  # English format
            r'/dm\d+/(?:id|en)/([^/]+)$',  # Domain with id/en
            r'/([^/]+)$'  # Just the ID at the end
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        raise ValueError("Invalid URL format")

    def extract_video_info(self, decoded_content):
        """Extract video information from decoded content."""
        video_urls = []
        thumbnail = None
        duration = 0

        # Extract video URLs for different resolutions
        url_patterns = {
            '720': [r"source842='(https[^']+)'", r'source842="(https[^"]+)"'],  # 842x480 maps to 720p
            '1080': [r"source1280='(https[^']+)'", r'source1280="(https[^"]+)"'],  # 1280x720 maps to 1080p
            '360': [r"source360='(https[^']+)'", r'source360="(https[^"]+)"']
        }

        for resolution, patterns in url_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, decoded_content)
                if match:
                    url = match.group(1)
                    # Extract actual resolution from URL if available
                    actual_resolution = int(resolution)  # Convert to int immediately
                    if '1280x720' in url:
                        actual_resolution = 1080
                    elif '842x480' in url:
                        actual_resolution = 720
                    elif '640x360' in url:
                        actual_resolution = 360
                    
                    video_urls.append({
                        'url': str(url),  # Ensure URL is a string
                        'resolution': actual_resolution,  # Already an integer
                        'bandwidth': actual_resolution * 1000  # Approximate bandwidth
                    })
                    break  # Found URL for this resolution, move to next

        # If no URLs found using patterns, try to find any m3u8 URLs
        if not video_urls:
            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', decoded_content)
            for url in url_matches:
                # Try to determine resolution from URL
                resolution = 720  # Default resolution
                if '1280x720' in url:
                    resolution = 1080
                elif '842x480' in url:
                    resolution = 720
                elif '640x360' in url:
                    resolution = 360
                
                video_urls.append({
                    'url': str(url),  # Ensure URL is a string
                    'resolution': resolution,  # Already an integer
                    'bandwidth': resolution * 1000  # Approximate bandwidth
                })

        # Sort URLs by resolution in descending order
        video_urls.sort(key=lambda x: x['resolution'], reverse=True)
        
        return video_urls, thumbnail, duration

    def decode_eval(self, encoded_text):
        """Extract and decode eval content."""
        try:
            # Find the eval line
            eval_match = re.search(r'eval\((.*)\)', encoded_text)
            if not eval_match:
                print("No eval content found in the text")
                # Try to find m3u8 URLs directly in the encoded text
                url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                if url_matches:
                    print(f"Found {len(url_matches)} URLs directly in the encoded text")
                    return encoded_text
                return None

            # Get the content inside eval()
            eval_content = eval_match.group(1)
            print(f"Found eval content: {eval_content[:100]}...")  # Print first 100 chars for debugging

            # If it's a function definition, extract it
            if eval_content.startswith('function'):
                try:
                    # Get the application path
                    app_path = None
                    if getattr(sys, 'frozen', False):
                        # Running in a bundle
                        app_path = os.path.dirname(sys.executable)
                        print(f"Running in bundle, app_path: {app_path}")
                    else:
                        # Running in normal Python environment
                        app_path = os.path.dirname(os.path.abspath(__file__))
                        print(f"Running in normal environment, app_path: {app_path}")
                    
                    # Try to find the JavaScript file in multiple locations
                    js_file_paths = [
                        # Current directory
                        'decode_packed.js',
                        
                        # Package directory
                        os.path.join(app_path, 'decode_packed.js'),
                        
                        # Resources directory in app bundle
                        os.path.join(app_path, '..', 'Resources', 'decode_packed.js'),
                        os.path.join(app_path, '..', '..', 'Resources', 'decode_packed.js'),
                        os.path.join(app_path, '..', '..', '..', 'Resources', 'decode_packed.js'),
                        
                        # MacOS directory in app bundle
                        os.path.join(app_path, 'decode_packed.js'),
                        os.path.join(app_path, '..', 'decode_packed.js'),
                        
                        # Development environment paths
                        os.path.join(os.getcwd(), 'decode_packed.js'),
                        os.path.join(os.getcwd(), 'bohep_downloader', 'decode_packed.js'),
                        os.path.join(os.getcwd(), '..', 'decode_packed.js'),
                        os.path.join(os.getcwd(), '..', 'bohep_downloader', 'decode_packed.js'),
                        
                        # Additional paths for packaged app
                        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'decode_packed.js'),
                        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '..', 'Resources', 'decode_packed.js'),
                        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '..', '..', 'Resources', 'decode_packed.js'),
                        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '..', '..', '..', 'Resources', 'decode_packed.js'),
                    ]
                    
                    # Print all paths being checked
                    print("Checking for decode_packed.js in the following locations:")
                    for path in js_file_paths:
                        print(f"  - {path} (exists: {os.path.exists(path)})")
                    
                    js_file_path = None
                    for path in js_file_paths:
                        if os.path.exists(path):
                            js_file_path = path
                            print(f"Using JavaScript file at: {js_file_path}")
                            break
                    
                    if not js_file_path:
                        print("Error: Could not find decode_packed.js file in any of the expected locations")
                        
                        # Try to create the file in a known location
                        try:
                            # Create Resources directory if it doesn't exist
                            resources_dir = os.path.join(app_path, '..', 'Resources')
                            if not os.path.exists(resources_dir):
                                os.makedirs(resources_dir)
                            
                            # Copy the file from the package to Resources
                            source_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decode_packed.js')
                            target_file = os.path.join(resources_dir, 'decode_packed.js')
                            
                            if os.path.exists(source_file):
                                print(f"Copying decode_packed.js from {source_file} to {target_file}")
                                shutil.copy(source_file, target_file)
                                js_file_path = target_file
                            else:
                                print(f"Source file not found: {source_file}")
                        except Exception as e:
                            print(f"Error creating decode_packed.js: {e}")
                        
                        # Try to extract URLs directly from the encoded text
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                        if url_matches:
                            print(f"Found {len(url_matches)} URLs directly in the encoded text")
                            return encoded_text
                        
                        # Try to extract URLs with a more lenient pattern
                        url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
                        if url_matches:
                            print(f"Found {len(url_matches)} potential URLs in the encoded text")
                            return encoded_text
                            
                        return None
                    
                    # Run Node.js to decode
                    print(f"Running Node.js with file: {js_file_path}")
                    try:
                        # Check if Node.js is available
                        node_path = None
                        for path in os.environ.get('PATH', '').split(os.pathsep):
                            potential_node = os.path.join(path, 'node')
                            if os.path.exists(potential_node) and os.access(potential_node, os.X_OK):
                                node_path = potential_node
                                break
                        
                        if not node_path:
                            print("Node.js not found in PATH, trying to find it in common locations")
                            common_node_paths = [
                                '/usr/local/bin/node',
                                '/usr/bin/node',
                                '/opt/homebrew/bin/node',
                                os.path.expanduser('~/.nvm/versions/node/current/bin/node'),
                                os.path.expanduser('~/.nvm/versions/node/lts/bin/node'),
                            ]
                            
                            for path in common_node_paths:
                                if os.path.exists(path) and os.access(path, os.X_OK):
                                    node_path = path
                                    print(f"Found Node.js at: {node_path}")
                                    break
                        
                        if not node_path:
                            print("Node.js not found, trying to extract URLs directly")
                            # Try to extract URLs directly from the encoded text
                            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                            if url_matches:
                                print(f"Found {len(url_matches)} URLs directly in the encoded text")
                                return encoded_text
                            
                            # Try to extract URLs with a more lenient pattern
                            url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
                            if url_matches:
                                print(f"Found {len(url_matches)} potential URLs in the encoded text")
                                return encoded_text
                                
                            return None
                        
                        # Run Node.js with the file
                        result = subprocess.run([node_path, js_file_path, eval_content], 
                                             capture_output=True, 
                                             text=True)
                        
                        if result.returncode == 0 and result.stdout:
                            decoded = result.stdout.strip()
                            print(f"Successfully decoded content: {decoded[:100]}...")  # Print first 100 chars
                            return decoded
                        else:
                            # Try to extract URLs directly from the error message or stdout
                            content = result.stderr or result.stdout
                            print(f"Node.js output: {content[:200]}...")  # Print first 200 chars
                            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', content)
                            if url_matches:
                                print(f"Found {len(url_matches)} URLs in Node.js output")
                                return content
                            
                            # Try to extract URLs with a more lenient pattern
                            url_matches = re.findall(r'https://[^\'"\s]+', content)
                            if url_matches:
                                print(f"Found {len(url_matches)} potential URLs in Node.js output")
                                return content
                            
                            # Try to extract URLs directly from the encoded text
                            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                            if url_matches:
                                print(f"Found {len(url_matches)} URLs directly in the encoded text")
                                return encoded_text
                            
                            # Try to extract URLs with a more lenient pattern
                            url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
                            if url_matches:
                                print(f"Found {len(url_matches)} potential URLs in the encoded text")
                                return encoded_text
                                
                            print("No URLs found in Node.js output or encoded text")
                            return None
                    except subprocess.SubprocessError as e:
                        print(f"Error running Node.js: {e}")
                        # Try to extract URLs directly from the encoded text
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                        if url_matches:
                            print(f"Found {len(url_matches)} URLs directly in the encoded text")
                            return encoded_text
                        
                        # Try to extract URLs with a more lenient pattern
                        url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
                        if url_matches:
                            print(f"Found {len(url_matches)} potential URLs in the encoded text")
                            return encoded_text
                            
                        return None
                except Exception as e:
                    print(f"Error decoding eval content: {e}")
                    # Try to extract URLs directly from the encoded text
                    url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                    if url_matches:
                        print(f"Found {len(url_matches)} URLs directly in the encoded text")
                        return encoded_text
                    
                    # Try to extract URLs with a more lenient pattern
                    url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
                    if url_matches:
                        print(f"Found {len(url_matches)} potential URLs in the encoded text")
                        return encoded_text
                        
                    return None

            # If it's base64 encoded
            elif 'atob' in eval_content:
                base64_match = re.search(r'atob\(["\']([^"\']+)["\']\)', eval_content)
                if base64_match:
                    try:
                        decoded = base64.b64decode(base64_match.group(1)).decode('utf-8')
                        print(f"Successfully decoded base64 content: {decoded[:100]}...")  # Print first 100 chars
                        return decoded
                    except Exception as e:
                        print(f"Error decoding base64 content: {e}")
                        # Try to extract URLs directly from the encoded text
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
                        if url_matches:
                            print(f"Found {len(url_matches)} URLs directly in the encoded text")
                            return encoded_text
                        return None

            # Try to extract URLs directly from the eval content
            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', eval_content)
            if url_matches:
                print(f"Found {len(url_matches)} URLs directly in the eval content")
                return eval_content
            
            # Try to extract URLs with a more lenient pattern
            url_matches = re.findall(r'https://[^\'"\s]+', eval_content)
            if url_matches:
                print(f"Found {len(url_matches)} potential URLs in the eval content")
                return eval_content

            print("Unrecognized eval content format")
            return None
        except Exception as e:
            print(f"Error in decode_eval: {e}")
            # Try to extract URLs directly from the encoded text
            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', encoded_text)
            if url_matches:
                print(f"Found {len(url_matches)} URLs directly in the encoded text")
                return encoded_text
            
            # Try to extract URLs with a more lenient pattern
            url_matches = re.findall(r'https://[^\'"\s]+', encoded_text)
            if url_matches:
                print(f"Found {len(url_matches)} potential URLs in the encoded text")
                return encoded_text
                
            return None

    def get_m3u8_url(self, page_url):
        """Get the m3u8 playlist URL from the page."""
        try:
            print(f"Fetching page: {page_url}")
            response = self.session.get(page_url)
            response.raise_for_status()
            
            # Find eval line in the response
            lines = response.text.split('\n')
            eval_line = None
            for line in lines:
                if 'eval(' in line:
                    eval_line = line.strip()
                    print(f"Found eval line: {eval_line[:100]}...")  # Print first 100 chars
                    break

            if not eval_line:
                print("Could not find eval content in the page, trying direct URL extraction")
                # Try to find m3u8 URLs directly in the page content
                url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', response.text)
                if url_matches:
                    print(f"Found {len(url_matches)} m3u8 URLs directly in the page content")
                    # Create video URL objects
                    video_urls = []
                    for url in url_matches:
                        # Try to determine resolution from URL
                        resolution = 720  # Default resolution
                        if '1280x720' in url or '1080' in url:
                            resolution = 1080
                        elif '842x480' in url or '720' in url:
                            resolution = 720
                        elif '640x360' in url or '360' in url:
                            resolution = 360
                        
                        video_urls.append({
                            'url': str(url),
                            'resolution': resolution,
                            'bandwidth': resolution * 1000
                        })
                    
                    # Sort by resolution
                    video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                    return video_urls
                
                # Try to find URLs with a more lenient pattern
                url_matches = re.findall(r'https://[^\'"\s]+', response.text)
                if url_matches:
                    print(f"Found {len(url_matches)} potential URLs in the page content")
                    # Filter for URLs that might be video-related
                    video_urls = []
                    for url in url_matches:
                        # Check if URL might be a video URL
                        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.ts', '.m4v', '.avi', '.mkv']):
                            # Try to determine resolution from URL
                            resolution = 720  # Default resolution
                            if '1280x720' in url or '1080' in url:
                                resolution = 1080
                            elif '842x480' in url or '720' in url:
                                resolution = 720
                            elif '640x360' in url or '360' in url:
                                resolution = 360
                            
                            video_urls.append({
                                'url': str(url),
                                'resolution': resolution,
                                'bandwidth': resolution * 1000
                            })
                    
                    if video_urls:
                        # Sort by resolution
                        video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                        return video_urls
                
                # Try to find URLs in script tags
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_content = script.string
                    if script_content:
                        # Try to find m3u8 URLs in script content
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', script_content)
                        if url_matches:
                            print(f"Found {len(url_matches)} m3u8 URLs in script tags")
                            # Create video URL objects
                            video_urls = []
                            for url in url_matches:
                                # Try to determine resolution from URL
                                resolution = 720  # Default resolution
                                if '1280x720' in url or '1080' in url:
                                    resolution = 1080
                                elif '842x480' in url or '720' in url:
                                    resolution = 720
                                elif '640x360' in url or '360' in url:
                                    resolution = 360
                                
                                video_urls.append({
                                    'url': str(url),
                                    'resolution': resolution,
                                    'bandwidth': resolution * 1000
                                })
                            
                            # Sort by resolution
                            video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                            return video_urls
                
                raise ValueError("Could not find eval content or m3u8 URLs in the page")

            decoded_content = self.decode_eval(eval_line)
            
            if not decoded_content:
                print("Failed to decode eval content, trying direct URL extraction")
                # Try to find m3u8 URLs directly in the page content
                url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', response.text)
                if url_matches:
                    print(f"Found {len(url_matches)} m3u8 URLs directly in the page content")
                    # Create video URL objects
                    video_urls = []
                    for url in url_matches:
                        # Try to determine resolution from URL
                        resolution = 720  # Default resolution
                        if '1280x720' in url or '1080' in url:
                            resolution = 1080
                        elif '842x480' in url or '720' in url:
                            resolution = 720
                        elif '640x360' in url or '360' in url:
                            resolution = 360
                        
                        video_urls.append({
                            'url': str(url),
                            'resolution': resolution,
                            'bandwidth': resolution * 1000
                        })
                    
                    # Sort by resolution
                    video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                    return video_urls
                
                # Try to find URLs with a more lenient pattern
                url_matches = re.findall(r'https://[^\'"\s]+', response.text)
                if url_matches:
                    print(f"Found {len(url_matches)} potential URLs in the page content")
                    # Filter for URLs that might be video-related
                    video_urls = []
                    for url in url_matches:
                        # Check if URL might be a video URL
                        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.ts', '.m4v', '.avi', '.mkv']):
                            # Try to determine resolution from URL
                            resolution = 720  # Default resolution
                            if '1280x720' in url or '1080' in url:
                                resolution = 1080
                            elif '842x480' in url or '720' in url:
                                resolution = 720
                            elif '640x360' in url or '360' in url:
                                resolution = 360
                            
                            video_urls.append({
                                'url': str(url),
                                'resolution': resolution,
                                'bandwidth': resolution * 1000
                            })
                    
                    if video_urls:
                        # Sort by resolution
                        video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                        return video_urls
                
                # Try to find URLs in script tags
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_content = script.string
                    if script_content:
                        # Try to find m3u8 URLs in script content
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', script_content)
                        if url_matches:
                            print(f"Found {len(url_matches)} m3u8 URLs in script tags")
                            # Create video URL objects
                            video_urls = []
                            for url in url_matches:
                                # Try to determine resolution from URL
                                resolution = 720  # Default resolution
                                if '1280x720' in url or '1080' in url:
                                    resolution = 1080
                                elif '842x480' in url or '720' in url:
                                    resolution = 720
                                elif '640x360' in url or '360' in url:
                                    resolution = 360
                                
                                video_urls.append({
                                    'url': str(url),
                                    'resolution': resolution,
                                    'bandwidth': resolution * 1000
                                })
                            
                            # Sort by resolution
                            video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                            return video_urls
                
                raise ValueError("Failed to decode eval content and no m3u8 URLs found in the page")

            # Extract video URLs and info
            video_urls, thumbnail, duration = self.extract_video_info(decoded_content)
            
            if not video_urls:
                print("No video URLs found in decoded content, trying direct URL extraction")
                # Try to find m3u8 URLs directly in the decoded content
                url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', decoded_content)
                if url_matches:
                    print(f"Found {len(url_matches)} m3u8 URLs in the decoded content")
                    # Create video URL objects
                    video_urls = []
                    for url in url_matches:
                        # Try to determine resolution from URL
                        resolution = 720  # Default resolution
                        if '1280x720' in url or '1080' in url:
                            resolution = 1080
                        elif '842x480' in url or '720' in url:
                            resolution = 720
                        elif '640x360' in url or '360' in url:
                            resolution = 360
                        
                        video_urls.append({
                            'url': str(url),
                            'resolution': resolution,
                            'bandwidth': resolution * 1000
                        })
                    
                    # Sort by resolution
                    video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                    return video_urls
                
                # Try to find URLs with a more lenient pattern
                url_matches = re.findall(r'https://[^\'"\s]+', decoded_content)
                if url_matches:
                    print(f"Found {len(url_matches)} potential URLs in the decoded content")
                    # Filter for URLs that might be video-related
                    video_urls = []
                    for url in url_matches:
                        # Check if URL might be a video URL
                        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.ts', '.m4v', '.avi', '.mkv']):
                            # Try to determine resolution from URL
                            resolution = 720  # Default resolution
                            if '1280x720' in url or '1080' in url:
                                resolution = 1080
                            elif '842x480' in url or '720' in url:
                                resolution = 720
                            elif '640x360' in url or '360' in url:
                                resolution = 360
                            
                            video_urls.append({
                                'url': str(url),
                                'resolution': resolution,
                                'bandwidth': resolution * 1000
                            })
                    
                    if video_urls:
                        # Sort by resolution
                        video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                        return video_urls
                
                # Try to find m3u8 URLs directly in the page content as a last resort
                url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', response.text)
                if url_matches:
                    print(f"Found {len(url_matches)} m3u8 URLs directly in the page content")
                    # Create video URL objects
                    video_urls = []
                    for url in url_matches:
                        # Try to determine resolution from URL
                        resolution = 720  # Default resolution
                        if '1280x720' in url or '1080' in url:
                            resolution = 1080
                        elif '842x480' in url or '720' in url:
                            resolution = 720
                        elif '640x360' in url or '360' in url:
                            resolution = 360
                        
                        video_urls.append({
                            'url': str(url),
                            'resolution': resolution,
                            'bandwidth': resolution * 1000
                        })
                    
                    # Sort by resolution
                    video_urls.sort(key=lambda x: x['resolution'], reverse=True)
                    return video_urls
                
                raise ValueError("No video URLs found in decoded content or page")

            # Ensure each URL info is a proper dictionary
            valid_urls = []
            for url_info in video_urls:
                # Rigorous check to ensure it's a dict with required keys and types
                if isinstance(url_info, dict) and \
                   'resolution' in url_info and isinstance(url_info['resolution'], int) and \
                   'url' in url_info and isinstance(url_info['url'], str):
                    valid_urls.append({
                        'resolution': url_info['resolution'],
                        'url': url_info['url'],
                        'bandwidth': int(url_info.get('bandwidth', 0))
                    })
                # Skip any item that doesn't strictly match the expected format

            # Sort by resolution - Now sorting only confirmed valid dictionaries
            try:
                valid_urls.sort(key=lambda x: x['resolution'], reverse=True)
            except KeyError as e:
                # This shouldn't happen with the checks above, but adding safety
                raise ValueError(f"Error sorting video URLs: {e}")
            except TypeError as e:
                # This shouldn't happen with the checks above, but adding safety
                raise ValueError(f"Error sorting video URLs (type issue): {e}")

            print(f"\nFound {len(valid_urls)} video qualities:")
            for url_info in valid_urls:
                # Safety check kept, though less likely needed now
                if isinstance(url_info, dict) and 'resolution' in url_info and 'url' in url_info:
                    print(f"{url_info['resolution']}p: {url_info['url']}")
                # else: Removed the debug print for malformed items

            return valid_urls.copy() # Return a copy for safety

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch page: {str(e)}")
        except Exception as e:
            raise

    def get_available_resolutions(self, m3u8_url):
        """Get available resolutions from m3u8 playlist."""
        try:
            playlist = m3u8.load(m3u8_url)
            resolutions = []
            
            if playlist.playlists:
                for stream in playlist.playlists:
                    resolution = stream.stream_info.resolution
                    bandwidth = stream.stream_info.bandwidth
                    uri = stream.uri
                    
                    # Handle relative URLs
                    if not uri.startswith('http'):
                        base_url = m3u8_url.rsplit('/', 1)[0]
                        uri = f"{base_url}/{uri}"
                    
                    # Extract the height as the resolution value
                    height = resolution[1] if resolution else 720
                    
                    resolutions.append({
                        'resolution': height,  # Store as integer
                        'bandwidth': bandwidth,
                        'url': uri
                    })
            
            return resolutions
            
        except Exception as e:
            raise Exception(f"Failed to parse m3u8 playlist: {str(e)}")

    def try_alternate_url_patterns(self, base_url):
        """Try different URL patterns for video segments."""
        patterns = [
            'video.m3u8',
            'index.m3u8',
            'playlist.m3u8',
            'master.m3u8',
            'stream.m3u8'
        ]
        
        base_url = base_url.rsplit('/', 1)[0]
        
        for pattern in patterns:
            url = f"{base_url}/{pattern}"
            try:
                response = self.session.get(url)
                if response.status_code == 200 and '#EXTINF' in response.text and '.ts' in response.text:
                    return url
            except Exception:
                continue
        
        return None

    def fetch_with_range(self, url, start=0, end=None):
        """Fetch content with range headers."""
        headers = self.session.headers.copy()
        if end is not None:
            headers['Range'] = f'bytes={start}-{end}'
        else:
            headers['Range'] = f'bytes={start}-'
        
        response = self.session.get(url, headers=headers)
        if response.status_code in [200, 206]:
            return response.content
        else:
            raise Exception(f"Failed to fetch content: HTTP {response.status_code}")

    def download_segments(self, base_url, segments, output_path):
        """Download segments and combine them into a video file."""
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            segment_files = []
            failed_segments = []
            
            print(f"\nDownloading {len(segments)} segments...")
            
            def download_segment(args):
                i, segment = args
                if not segment.uri.startswith('http'):
                    segment_url = base_url + segment.uri
                else:
                    segment_url = segment.uri
                
                # Try both .ts and .jpeg extensions
                extensions = ['.ts', '.jpeg', '.mp4']
                segment_data = None
                
                for ext in extensions:
                    try:
                        url = segment_url.rsplit('.', 1)[0] + ext
                        try:
                            segment_data = self.fetch_with_range(url)
                            if segment_data:
                                break
                        except Exception:
                            # Try without range header
                            self.session.headers.pop('Range', None)
                            response = self.session.get(url)
                            if response.status_code == 200 and len(response.content) > 0:
                                segment_data = response.content
                                break
                    except Exception:
                        continue
                
                if segment_data:
                    segment_file = os.path.join(temp_dir, f"segment_{i:04d}.ts")
                    with open(segment_file, 'wb') as f:
                        f.write(segment_data)
                    return i, segment_file
                else:
                    return i, None
            
            # Create a list of arguments for each segment
            segment_args = list(enumerate(segments, 1))
            
            # Use ThreadPoolExecutor for concurrent downloads
            max_workers = min(20, len(segments))
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            try:
                # Submit all tasks and create a progress bar
                futures = {executor.submit(download_segment, args): args[0] for args in segment_args}
                
                # Process completed downloads with progress bar
                completed = 0
                start_time = time.time()
                with tqdm(total=len(segments), desc="Downloading segments") as pbar:
                    for future in concurrent.futures.as_completed(futures):
                        # Check if download was cancelled
                        if self.cancelled:
                            print("\nDownload cancelled by user")
                            executor.shutdown(wait=False)
                            raise Exception("Download cancelled by user")
                            
                        i, result = future.result()
                        if result:
                            segment_files.append((i, result))
                        else:
                            failed_segments.append(i)
                        
                        completed += 1
                        elapsed_time = time.time() - start_time
                        speed = completed / elapsed_time if elapsed_time > 0 else 0
                        eta = (len(segments) - completed) / speed if speed > 0 else 0
                        
                        # Update progress callback with detailed information
                        if self.progress_callback:
                            progress_info = {
                                'completed': completed,
                                'total': len(segments),
                                'percentage': (completed / len(segments)) * 100,
                                'speed': speed,
                                'eta': eta
                            }
                            self.progress_callback(progress_info)
                        
                        pbar.update(1)
            finally:
                # Ensure executor is properly shut down
                executor.shutdown(wait=True)
            
            # Check if download was cancelled after all segments are processed
            if self.cancelled:
                raise Exception("Download cancelled by user")
                
            if failed_segments:
                print(f"\nFailed to download segments: {failed_segments}")
                raise Exception(f"Failed to download {len(failed_segments)} segments")
            
            # Sort segments by index before combining
            segment_files.sort(key=lambda x: x[0])
            segment_files = [f[1] for f in segment_files]
            
            print("\nCombining segments into final video...")
            
            # Create a file list for FFmpeg
            file_list = os.path.join(temp_dir, "file_list.txt")
            with open(file_list, 'w') as f:
                for segment_file in segment_files:
                    f.write(f"file '{segment_file}'\n")
            
            # Use FFmpeg to combine segments
            try:
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', file_list,
                    '-c', 'copy',
                    output_path
                ]
                
                process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if process.returncode != 0:
                    raise Exception("Failed to combine segments with FFmpeg")
                
            except Exception as e:
                # Fallback to direct file concatenation if FFmpeg fails
                print("Falling back to direct file concatenation...")
                with open(output_path, 'wb') as outfile:
                    for segment_file in tqdm(segment_files, desc="Combining segments"):
                        # Check if download was cancelled during merging
                        if self.cancelled:
                            raise Exception("Download cancelled by user")
                            
                        with open(segment_file, 'rb') as infile:
                            outfile.write(infile.read())
            
            print("Cleaning up temporary files...")
            for file in segment_files:
                try:
                    os.remove(file)
                except:
                    pass
            try:
                os.remove(file_list)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            
            print(f"\nDownload completed! File saved as: {output_path}")
            
        except Exception as e:
            print(f"Error downloading segments: {str(e)}")
            # Clean up temp directory in case of error
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            raise

    def download_video(self, url, output_path):
        """Download video using segment-by-segment approach."""
        try:
            # Get base URL for segments
            base_url = url.rsplit('/', 1)[0] + '/'
            
            # Fetch and parse the playlist
            try:
                # Remove Range header for playlist request
                headers = self.session.headers.copy()
                headers.pop('Range', None)
                response = self.session.get(url, headers=headers)
                
                if response.status_code not in [200, 206]:
                    raise Exception(f"Failed to fetch playlist: HTTP {response.status_code}")
                playlist_content = response.content
            except Exception as e:
                raise Exception(f"Failed to fetch playlist: {str(e)}")
            
            # Decode playlist content
            try:
                playlist_text = playlist_content.decode()
            except UnicodeDecodeError:
                playlist_text = playlist_content.decode('utf-8', errors='ignore')
            
            playlist = m3u8.loads(playlist_text)
            if not playlist.segments:
                raise Exception("No segments found in playlist")
            
            # Download and combine segments
            self.download_segments(base_url, playlist.segments, output_path)
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")

    def get_output_filename(self) -> str:
        """Return the path of the downloaded video file."""
        return str(self.output_file) if self.output_file else ""
    
    def download(self, url: str, quality: str = "720p", save_dir: Optional[str] = None, progress_callback: Optional[Callable[[float], None]] = None) -> None:
        """Download a video from the given URL."""
        self.progress_callback = progress_callback
        self.reset_cancellation()
        
        try:
            # Extract video ID
            video_id = self.extract_video_id(url)
            if not video_id:
                raise ValueError("Invalid URL format")
            
            # Set output directory
            if not save_dir:
                save_dir = str(Path.home() / "Downloads")
            
            # Create output directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Convert target quality to integer (e.g., "720p" -> 720)
            target_resolution = int(quality.replace('p', ''))
            
            # Get fresh video URLs
            video_urls = self.get_m3u8_url(url)
            if not video_urls:
                raise ValueError("No video URLs found")
            
            # Find exact quality match first
            selected_url = None
            selected_resolution = None
            
            # Print available qualities for debugging
            print("Available qualities:", [f"{url_info.get('resolution')}p" for url_info in video_urls if isinstance(url_info, dict)])
            print("Target resolution:", target_resolution)
            
            # Find exact match or closest quality
            for url_info in video_urls:
                if not isinstance(url_info, dict):
                    continue
                    
                resolution = url_info.get('resolution')
                if not isinstance(resolution, (int, float)):
                    continue
                    
                video_url = url_info.get('url')
                if not video_url:
                    continue
                
                if resolution == target_resolution:
                    selected_url = video_url
                    selected_resolution = resolution
                    break
                elif not selected_resolution or abs(resolution - target_resolution) < abs(selected_resolution - target_resolution):
                    selected_url = video_url
                    selected_resolution = resolution
            
            if not selected_url:
                raise ValueError("Could not find suitable video quality")
            
            # Set output filename
            output_file = os.path.join(save_dir, f"{video_id}-{selected_resolution}p.mp4")
            
            # Download the video
            if progress_callback:
                progress_callback({'percentage': 10, 'completed': 0, 'total': 0, 'speed': 0, 'eta': 0})
            
            print(f"\nDownloading video to: {output_file}")
            print(f"Selected quality: {selected_resolution}p")
            print(f"Selected URL: {selected_url}")
            
            self.download_video(selected_url, output_file)
            
            if progress_callback:
                progress_callback({'percentage': 100, 'completed': 0, 'total': 0, 'speed': 0, 'eta': 0})
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"\nDownload completed! File saved as: {output_file}")
            else:
                raise Exception("Download failed - output file is empty or does not exist")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            raise
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

def main():
    if len(sys.argv) != 2:
        print("Usage: python video_downloader.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = BohepDownloader()
    downloader.download(url)

if __name__ == "__main__":
    main() 