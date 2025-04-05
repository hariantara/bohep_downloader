import os
import sys
import encodings
import multiprocessing
import atexit

def setup_python_path():
    """Set up Python path to include necessary modules."""
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        bundle_dir = sys._MEIPASS
    else:
        # Running as a Python script
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add bundle directory to Python path
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
    
    # Add lib directory if it exists
    lib_dir = os.path.join(bundle_dir, 'lib')
    if os.path.exists(lib_dir) and lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

def initialize_encodings():
    """Initialize the encodings module."""
    if not hasattr(encodings, '_cache'):
        encodings._cache = {}
    if 'ascii' not in encodings._cache:
        encodings.search_function('ascii')
    if 'utf_8' not in encodings._cache:
        encodings.search_function('utf_8')
    if 'latin_1' not in encodings._cache:
        encodings.search_function('latin_1')

def setup_multiprocessing():
    """Set up multiprocessing to handle resource cleanup properly."""
    if hasattr(multiprocessing, 'resource_tracker'):
        # Disable resource tracker warnings
        multiprocessing.resource_tracker._resource_tracker._warn = lambda *args, **kwargs: None
        
        # Register cleanup handler
        def cleanup_resources():
            try:
                if hasattr(multiprocessing, 'resource_tracker'):
                    tracker = multiprocessing.resource_tracker._resource_tracker
                    if hasattr(tracker, '_resource_tracker'):
                        tracker._resource_tracker.cleanup()
            except Exception:
                pass
        
        atexit.register(cleanup_resources)

def main():
    """Main initialization function."""
    setup_python_path()
    initialize_encodings()
    setup_multiprocessing()

if __name__ == '__main__':
    main() 