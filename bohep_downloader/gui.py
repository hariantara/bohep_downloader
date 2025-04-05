import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from bohep_downloader.downloader import BohepDownloader
from pathlib import Path
import re
from queue import Queue

class BohepDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bohep Downloader")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Set theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors - modern color scheme
        bg_color = "#f5f5f5"
        accent_color = "#3498db"
        text_color = "#333333"
        success_color = "#2ecc71"
        error_color = "#e74c3c"
        
        # Configure styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), background=accent_color, foreground="white")
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=accent_color)
        style.configure('Status.TLabel', font=('Segoe UI', 9), foreground=text_color)
        
        # Configure progress bar
        style.configure('TProgressbar', background=accent_color, troughcolor='#e0e0e0', borderwidth=0)
        
        # Configure combobox
        style.configure('TCombobox', font=('Segoe UI', 10))
        
        # Set root background
        self.root.configure(bg=bg_color)
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with modern styling
        title_label = ttk.Label(main_frame, text="Bohep Downloader", style='Title.TLabel')
        title_label.pack(pady=(0, 25))
        
        # URL input frame with card-like appearance
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        url_label = ttk.Label(url_frame, text="Video URL:", font=('Segoe UI', 10, 'bold'))
        url_label.pack(anchor=tk.W, pady=(0, 5))
        
        url_entry_frame = ttk.Frame(url_frame)
        url_entry_frame.pack(fill=tk.X)
        
        self.url_entry = ttk.Entry(url_entry_frame, font=('Segoe UI', 10))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        
        # Add URL check button with accent color
        self.check_url_button = ttk.Button(url_entry_frame, text="Check URL", command=self.check_url)
        self.check_url_button.pack(side=tk.LEFT, padx=(10, 0), ipadx=10, ipady=5)
        
        # Quality selection frame
        quality_frame = ttk.Frame(main_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 15))
        
        quality_label = ttk.Label(quality_frame, text="Quality:", font=('Segoe UI', 10, 'bold'))
        quality_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.quality_var = tk.StringVar()
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, state="readonly", font=('Segoe UI', 10))
        self.quality_combo.pack(fill=tk.X, ipady=5)
        
        # Download location frame
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill=tk.X, pady=(0, 15))
        
        location_label = ttk.Label(location_frame, text="Save to:", font=('Segoe UI', 10, 'bold'))
        location_label.pack(anchor=tk.W, pady=(0, 5))
        
        location_entry_frame = ttk.Frame(location_frame)
        location_entry_frame.pack(fill=tk.X)
        
        self.location_entry = ttk.Entry(location_entry_frame, font=('Segoe UI', 10))
        self.location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.location_entry.insert(0, str(Path.home() / "Downloads"))
        
        # Store browse button as instance variable
        self.browse_button = ttk.Button(location_entry_frame, text="Browse", command=self.browse_location)
        self.browse_button.pack(side=tk.LEFT, padx=(10, 0), ipadx=10, ipady=5)
        
        # Progress section with card-like appearance
        progress_section = ttk.Frame(main_frame)
        progress_section.pack(fill=tk.X, pady=(0, 20))
        
        progress_label = ttk.Label(progress_section, text="Download Progress", font=('Segoe UI', 10, 'bold'))
        progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar with modern styling
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_section, variable=self.progress_var, maximum=100, style='TProgressbar')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # Progress details with modern font
        self.progress_details = ttk.Label(progress_section, text="", font=('Segoe UI', 9))
        self.progress_details.pack(fill=tk.X, pady=(0, 5))
        
        # Status label with modern styling
        self.status_label = ttk.Label(main_frame, text="Ready", style='Status.TLabel')
        self.status_label.pack(pady=(0, 15))
        
        # Button frame with modern spacing
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Center the buttons
        button_container = ttk.Frame(button_frame)
        button_container.pack(expand=True)
        
        # Download button
        self.download_button = ttk.Button(button_container, text="Download", command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 10), ipadx=15, ipady=8)
        
        # Cancel button
        self.cancel_button = ttk.Button(button_container, text="Cancel", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, ipadx=15, ipady=8)
        
        # Initialize downloader
        self.downloader = None
        self.download_thread = None
        self.available_qualities = []
        self.video_urls = None  # Store video URLs after checking
        self.is_downloading = False
        
        # Add hover effects to buttons
        self.add_hover_effects()
        
    def add_hover_effects(self):
        """Add hover effects to buttons for better interactivity."""
        def on_enter(e):
            e.widget.state(['active'])
            
        def on_leave(e):
            e.widget.state(['!active'])
            
        for button in [self.check_url_button, self.download_button, self.cancel_button, self.browse_button]:
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            
    def check_url(self):
        """Check URL and update available qualities."""
        try:
            url = self.url_entry.get().strip()
            if not url:
                raise ValueError("Please enter a video URL")
            
            self.check_url_button.config(state=tk.DISABLED)
            self.update_status("Checking URL...")
            
            # Create downloader instance
            self.downloader = BohepDownloader()
            
            # Get video URLs and store them
            self.video_urls = self.downloader.get_m3u8_url(url)
            
            if not self.video_urls:
                raise ValueError("No video URLs found")
            
            # Update available qualities
            self.available_qualities = []
            for url_info in self.video_urls:
                if isinstance(url_info, dict) and 'resolution' in url_info:
                    resolution = url_info['resolution']
                    if isinstance(resolution, (int, float)):
                        self.available_qualities.append(f"{resolution}p")
            
            # Remove duplicates and sort
            self.available_qualities = sorted(list(set(self.available_qualities)), 
                                           key=lambda x: int(x.replace('p', '')), 
                                           reverse=True)
            
            if not self.available_qualities:
                raise ValueError("No valid qualities found")
            
            self.quality_combo['values'] = self.available_qualities
            
            # Select highest quality by default
            if self.available_qualities:
                self.quality_var.set(self.available_qualities[0])
            
            self.update_status("URL checked successfully")
            self.check_url_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.update_status("Error checking URL")
            messagebox.showerror("Error", str(e))
            self.check_url_button.config(state=tk.NORMAL)
            self.downloader = None
            self.video_urls = None
    
    def browse_location(self):
        directory = filedialog.askdirectory(initialdir=self.location_entry.get())
        if directory:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, directory)
    
    def update_progress(self, progress_data):
        """Update progress bar and details."""
        try:
            if isinstance(progress_data, dict):
                # Handle detailed progress data
                percentage = progress_data.get('percentage', 0)
                completed = progress_data.get('completed', 0)
                total = progress_data.get('total', 0)
                speed = progress_data.get('speed', 0)
                eta = progress_data.get('eta', 0)
                stage = progress_data.get('stage', 'download')
                
                # Update progress bar
                self.progress_var.set(percentage)
                
                # Update progress details with terminal-like format
                if total > 0:
                    if stage == 'download':
                        details = f"Downloading segments: {completed}/{total} ({percentage:.1f}%)"
                        if speed and speed > 0:
                            details += f" | Speed: {speed:.1f} segments/s"
                        if eta and eta > 0:
                            details += f" | ETA: {eta:.0f}s"
                    elif stage == 'combine':
                        details = f"Combining segments: {percentage:.1f}%"
                    elif stage == 'segment':
                        # Show segment download progress
                        details = f"Downloading segment: {completed}/{total} bytes ({percentage:.1f}%)"
                    else:
                        details = f"Processing: {percentage:.1f}%"
                    self.progress_details.config(text=details)
                
                # Update status based on stage
                if stage == 'download':
                    if percentage < 10:
                        self.update_status("Preparing download...")
                    else:
                        self.update_status("Downloading segments...")
                elif stage == 'combine':
                    self.update_status("Combining segments...")
                elif stage == 'segment':
                    self.update_status("Downloading segment...")
                elif stage == 'complete':
                    self.update_status("Download complete!")
            else:
                # Handle simple percentage updates
                self.progress_var.set(progress_data)
                if progress_data < 100:
                    self.progress_details.config(text=f"Processing: {progress_data:.1f}%")
            
            # Force GUI update
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating progress: {e}")
            # Don't raise the error to avoid breaking the download
            
    def reset_progress(self):
        """Reset progress bar and details after download completion."""
        self.progress_var.set(0)
        self.progress_details.config(text="")
        self.update_status("Ready")
    
    def update_status(self, status):
        self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def download_complete(self, success, message):
        """Handle download completion."""
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.check_url_button.config(state=tk.NORMAL)  # Re-enable URL check
        
        # Reset progress bar and details
        self.progress_var.set(0)
        self.progress_details.config(text="")
        
        # Reset status
        self.update_status("Ready")
        
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
    
    def cancel_download(self):
        """Cancel the current download operation."""
        if self.is_downloading and self.downloader:
            self.update_status("Cancelling download...")
            self.downloader.cancel()
            self.cancel_button.config(state=tk.DISABLED)
            self.check_url_button.config(state=tk.NORMAL)  # Re-enable URL check
    
    def download_video(self):
        """Download the video in a separate thread."""
        try:
            # Check if already downloading
            if self.is_downloading:
                self.update_status("A download is already in progress")
                return
                
            url = self.url_entry.get().strip()
            if not url:
                raise ValueError("Please enter a video URL")
            
            # Get selected quality
            quality = self.quality_var.get()
            if not quality:
                raise ValueError("Please select a video quality")
            
            # Get save location
            save_dir = self.location_entry.get().strip()
            if not save_dir:
                save_dir = str(Path.home() / "Downloads")
            
            # Ensure we have a valid downloader instance
            if not self.downloader:
                self.downloader = BohepDownloader()
            
            # Reset cancellation flag
            self.downloader.reset_cancellation()
            
            # Start download
            self.is_downloading = True
            self.update_status("Preparing download...")
            self.root.update_idletasks()  # Force GUI update
            
            # Create a simple progress callback that directly updates the GUI
            def progress_callback(progress_data):
                # Use a simple function to avoid recursion
                def update():
                    self.update_progress(progress_data)
                # Schedule the update on the main thread
                self.root.after(0, update)
            
            # Download with progress updates
            self.downloader.download(
                url=url,
                quality=quality,
                save_dir=save_dir,
                progress_callback=progress_callback
            )
            
            # Check if download was cancelled
            if self.downloader.is_cancelled():
                self.download_complete(False, "Download cancelled by user")
            else:
                # Download completed successfully
                self.download_complete(True, "Download completed successfully!")
            
        except Exception as e:
            self.download_complete(False, str(e))
        finally:
            self.is_downloading = False
            # Ensure UI is reset even if there's an error
            self.root.after(0, self.reset_progress)
    
    def extract_video_id(self, url):
        """Extract video ID from URL."""
        patterns = [
            r'/id/([^/]+)$',
            r'/en/([^/]+)$',
            r'/dm\d+/(?:id|en)/([^/]+)$',
            r'/([^/]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return 'video'  # fallback name
    
    def start_download(self):
        """Start the download process in a separate thread."""
        if not self.quality_var.get():
            messagebox.showerror("Error", "Please check URL and select quality first")
            return
            
        if self.is_downloading:
            return
            
        # Disable download button and enable cancel button
        self.download_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.check_url_button.config(state=tk.DISABLED)  # Disable URL check during download
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_details.config(text="")
        
        # Start download in a separate thread
        self.download_thread = threading.Thread(target=self.download_video)
        self.download_thread.daemon = True
        self.download_thread.start()

def main():
    root = tk.Tk()
    app = BohepDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 