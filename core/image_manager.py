import os
import threading
import queue
import time
from PIL import Image, ImageTk

class ImageManager:
    """Manages image loading, caching, and navigation"""
    def __init__(self):
        self.images_folder = ""
        self.image_files = []
        self.current_image_index = 0
        self.current_image = None
        self.photo_image = None
        self.thumbnail_cache = {}
        self.current_batch_start = 0
        self.batch_size = 20
        self.loading_thread = None
        self.thumbnail_queue = queue.Queue()
        self.stop_loading = threading.Event()
    
    def load_images_from_folder(self, folder_path):
        """Load images from the specified folder"""
        if not os.path.exists(folder_path):
            return False
        
        self.images_folder = folder_path
        self.image_files = []
        self.thumbnail_cache = {}
        
        # Find supported image files
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp')):
                self.image_files.append(file)
        
        # Sort files for consistent ordering
        self.image_files.sort()
        
        return len(self.image_files) > 0
    
    def get_current_image_path(self):
        """Get path to the current image"""
        if not self.image_files or self.current_image_index < 0 or self.current_image_index >= len(self.image_files):
            return None
        
        return os.path.join(self.images_folder, self.image_files[self.current_image_index])
    
    def load_current_image(self):
        """Load the current image"""
        image_path = self.get_current_image_path()
        if not image_path:
            return None
        
        try:
            # Close previous image if it exists
            if self.current_image:
                self.current_image.close()
            
            # Load image
            self.current_image = Image.open(image_path)
            return self.current_image
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def start_thumbnail_loading(self):
        """Start background thread for thumbnail loading"""
        if not self.images_folder or not self.image_files:
            return
        
        # Clear stop flag
        self.stop_loading.clear()
        
        # Start loading thread if not already running
        if not self.loading_thread or not self.loading_thread.is_alive():
            self.loading_thread = threading.Thread(
                target=self._thumbnail_loader_thread,
                daemon=True
            )
            self.loading_thread.start()
    
    def stop_thumbnail_loading(self):
        """Stop thumbnail loading thread"""
        if self.loading_thread and self.loading_thread.is_alive():
            self.stop_loading.set()
            self.loading_thread.join(1.0)  # Wait for thread to finish
    
    def _thumbnail_loader_thread(self):
        """Background thread for loading thumbnails"""
        for i in range(self.current_batch_start, min(self.current_batch_start + self.batch_size, len(self.image_files))):
            if self.stop_loading.is_set():
                break
            
            if i not in self.thumbnail_cache:
                try:
                    image_path = os.path.join(self.images_folder, self.image_files[i])
                    with Image.open(image_path) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Create thumbnail
                        img.thumbnail((160, 120), Image.Resampling.LANCZOS)
                        # We'll use a queue to pass the processed thumbnail to the main thread
                        self.thumbnail_queue.put((i, img.copy()))
                    
                    # Small delay to not hog CPU
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"Error creating thumbnail for {self.image_files[i]}: {e}")
    
    def load_more_thumbnails(self):
        """Load the next batch of thumbnails"""
        if self.current_batch_start + self.batch_size < len(self.image_files):
            self.current_batch_start += self.batch_size
            self.start_thumbnail_loading()
            return True
        return False
    
    def next_image(self):
        """Navigate to next image"""
        if not self.image_files:
            return False
        
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            return True
        return False
    
    def previous_image(self):
        """Navigate to previous image"""
        if not self.image_files:
            return False
        
        if self.current_image_index > 0:
            self.current_image_index -= 1
            return True
        return False
    
    def jump_to_image(self, index):
        """Jump directly to an image by its index"""
        if not self.image_files:
            return False
        
        # Make sure index is valid
        if index < 0 or index >= len(self.image_files):
            return False
        
        self.current_image_index = index
        return True
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_thumbnail_loading()
        if self.current_image:
            self.current_image.close()
        self.thumbnail_cache.clear()
