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

class VideoDownloader:
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

    def extract_video_id(self, url):
        """Extract video ID from the URL."""
        match = re.search(r'/id/([^/]+)$', url)
        if not match:
            raise ValueError("Invalid URL format")
        return match.group(1)

    def extract_video_info(self, decoded_content):
        """Extract video information from decoded content."""
        video_urls = []
        thumbnail = None
        duration = 0

        # Extract video URLs for different resolutions
        url_patterns = {
            1080: [r"source1280='(https[^']+)'", r'source1280="(https[^"]+)"'],
            720: [r"source842='(https[^']+)'", r'source842="(https[^"]+)"'],
            360: [r"source360='(https[^']+)'", r'source360="(https[^"]+)"']
        }

        for resolution, patterns in url_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, decoded_content)
                if match:
                    url = match.group(1)
                    video_urls.append({
                        'url': url,
                        'resolution': resolution,
                        'bandwidth': resolution * 1000  # Approximate bandwidth based on resolution
                    })
                    break  # Found URL for this resolution, move to next

        # If no URLs found using patterns, try to find any m3u8 URLs
        if not video_urls:
            url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', decoded_content)
            for url in url_matches:
                # Try to determine resolution from URL
                resolution = 720  # Default resolution
                if '1280x720' in url:
                    resolution = 720
                elif '842x480' in url:
                    resolution = 480
                elif '640x360' in url:
                    resolution = 360
                
                video_urls.append({
                    'url': url,
                    'resolution': resolution,
                    'bandwidth': resolution * 1000
                })

        # Extract thumbnail
        thumbnail_patterns = [
            r"poster='([^']+)'",
            r'poster="([^"]+)"',
            r"thumbnail='([^']+)'",
            r'thumbnail="([^"]+)"',
            r"image='([^']+)'",
            r'image="([^"]+)"'
        ]

        for pattern in thumbnail_patterns:
            match = re.search(pattern, decoded_content)
            if match:
                thumbnail = match.group(1)
                break

        # Extract duration
        duration_patterns = [
            r'duration=([0-9.]+)',
            r"duration:'([0-9.]+)'",
            r'duration:"([0-9.]+)"',
            r'length:([0-9.]+)',
            r'Duration:\s*([0-9.]+)',
            r'videoDuration[\'"\s:]+([0-9.]+)',
            r'video_duration[\'"\s:]+([0-9.]+)',
            r'duration[\'"\s:]+([0-9:]+)'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, decoded_content)
            if match:
                try:
                    duration_str = match.group(1)
                    if ':' in duration_str:
                        # Convert time format (HH:MM:SS or MM:SS) to seconds
                        parts = duration_str.split(':')
                        if len(parts) == 2:  # MM:SS
                            duration = int(parts[0]) * 60 + int(parts[1])
                        elif len(parts) == 3:  # HH:MM:SS
                            duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    else:
                        duration = float(duration_str)
                        # If duration is in milliseconds, convert to seconds
                        if duration > 10000:
                            duration = duration / 1000
                    break
                except ValueError:
                    continue

        # Sort URLs by resolution
        video_urls.sort(key=lambda x: x['resolution'])
        
        return video_urls, thumbnail, duration

    def decode_eval(self, encoded_text):
        """Extract and decode eval content."""
        try:
            # Find the eval line
            eval_match = re.search(r'eval\((.*)\)', encoded_text)
            if not eval_match:
                return None

            # Get the content inside eval()
            eval_content = eval_match.group(1)

            # If it's a function definition, extract it
            if eval_content.startswith('function'):
                try:
                    # Run Node.js to decode
                    result = subprocess.run(['node', 'decode_packed.js', eval_content], 
                                         capture_output=True, 
                                         text=True)
                    
                    if result.returncode == 0 and result.stdout:
                        decoded = result.stdout.strip()
                        return decoded
                    else:
                        # Try to extract URLs directly from the error message or stdout
                        content = result.stderr or result.stdout
                        url_matches = re.findall(r'https://[^\'"\s]+\.m3u8', content)
                        if url_matches:
                            return content
                        return None
                except Exception as e:
                    return None

            # If it's base64 encoded
            elif 'atob' in eval_content:
                base64_match = re.search(r'atob\(["\']([^"\']+)["\']\)', eval_content)
                if base64_match:
                    try:
                        decoded = base64.b64decode(base64_match.group(1)).decode('utf-8')
                        return decoded
                    except:
                        return None

            return None
        except Exception as e:
            return None

    def get_m3u8_url(self, page_url):
        """Get the m3u8 playlist URL from the page."""
        try:
            response = self.session.get(page_url)
            response.raise_for_status()
            
            # Find eval line in the response
            lines = response.text.split('\n')
            eval_line = None
            for line in lines:
                if 'eval(' in line:
                    eval_line = line.strip()
                    break

            if not eval_line:
                raise ValueError("Could not find eval content in the page")

            decoded_content = self.decode_eval(eval_line)
            
            if not decoded_content:
                raise ValueError("Failed to decode eval content")

            # Extract video URLs and info
            video_urls, thumbnail, duration = self.extract_video_info(decoded_content)
            
            if not video_urls:
                raise ValueError("No video URLs found in decoded content")

            print(f"\nFound {len(video_urls)} video qualities:")
            for url_info in video_urls:
                print(f"{url_info['resolution']}p: {url_info['url']}")

            # Return the URLs for further processing
            return video_urls

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
                    
                    resolutions.append({
                        'resolution': f"{resolution[0]}x{resolution[1]}",
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
            max_workers = min(20, len(segments))  # Increased to 20 concurrent workers
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks and create a progress bar
                futures = {executor.submit(download_segment, args): args[0] for args in segment_args}
                
                # Process completed downloads with progress bar
                with tqdm(total=len(segments), desc="Downloading segments") as pbar:
                    for future in concurrent.futures.as_completed(futures):
                        i, result = future.result()
                        if result:
                            segment_files.append((i, result))
                        else:
                            failed_segments.append(i)
                        pbar.update(1)
            
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
                os.rmdir(temp_dir)
            except:
                pass
            
            print(f"\nDownload completed! File saved as: {output_path}")
            
        except Exception as e:
            print(f"Error downloading segments: {str(e)}")
            raise

    def download_video(self, url, output_path):
        """Download video using segment-by-segment approach."""
        try:
            # Try to find a valid m3u8 URL
            alternate_url = self.try_alternate_url_patterns(url)
            if alternate_url:
                url = alternate_url
            
            # Fetch and parse the playlist
            try:
                playlist_content = self.fetch_with_range(url)
            except Exception:
                # Try without range header
                self.session.headers.pop('Range', None)
                response = self.session.get(url)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch playlist: HTTP {response.status_code}")
                playlist_content = response.content
            
            playlist = m3u8.loads(playlist_content.decode())
            if not playlist.segments:
                raise Exception("No segments found in playlist")
            
            base_url = url.rsplit('/', 1)[0] + '/'
            
            # Download and combine segments
            self.download_segments(base_url, playlist.segments, output_path)
            
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")

    def download(self, url):
        """Main download function."""
        try:
            # Extract video ID
            video_id = self.extract_video_id(url)
            print(f"Video ID: {video_id}")

            # Get video URLs
            print("Fetching video URLs...")
            video_urls = self.get_m3u8_url(url)
            
            if not video_urls:
                raise Exception("No video URLs found")
            
            # Display available resolutions
            print("\nAvailable resolutions:")
            for i, url_info in enumerate(video_urls, 1):
                print(f"{i}. {url_info['resolution']}p ({url_info['bandwidth']/1000:.1f} Kbps)")
            
            # Get user choice
            while True:
                try:
                    choice = int(input("\nSelect resolution (enter number): ")) - 1
                    if 0 <= choice < len(video_urls):
                        break
                    print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

            selected_url = video_urls[choice]
            output_filename = f"{video_id}-{selected_url['resolution']}p.mp4"
            output_path = os.path.join(self.download_dir, output_filename)

            print(f"\nDownloading video to: {output_path}")
            self.download_video(selected_url['url'], output_path)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"\nDownload completed! File saved as: {output_filename}")
            else:
                raise Exception("Download failed - output file is empty or does not exist")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python video_downloader.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = VideoDownloader()
    downloader.download(url)

if __name__ == "__main__":
    main() 