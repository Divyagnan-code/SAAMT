import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

# Import UI modules
from ui.styles import ModernColors
from ui.sidebar import Sidebar
from ui.toolbar import Toolbar
from ui.canvas import CanvasArea
from ui.controls import ControlPanel

# Import core modules
from core.image_manager import ImageManager
from core.annotation_manager import AnnotationManager
from core.model_manager import ModelManager
from core.undo_manager import UndoRedoManager

class AnnotationApp:
    """Main application controller"""
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced AI Annotation Tool")
        self.root.geometry("1800x1200")
        self.root.configure(bg=ModernColors.DARK_BG)
        
        # Configure ttk styles
        self.setup_styles()
        
        # Initialize managers
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_manager = ModelManager(self.script_dir)
        self.image_manager = ImageManager()
        self.annotation_manager = AnnotationManager()
        self.undo_manager = UndoRedoManager()
        
        # Drawing and editing state
        self.drawing = False
        self.editing = False
        self.selected_annotation_id = None
        self.selected_handle = None
        self.boxes_visible = True
        
        # Setup UI components
        self.setup_ui()
        
        # Connect event handlers
        self.connect_events()
    
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.configure('TScale', background=ModernColors.DARKER_BG)
        style.configure('TCombobox', background=ModernColors.SIDEBAR_BG, fieldbackground=ModernColors.DARK_BG, foreground=ModernColors.TEXT_PRIMARY)
        style.map('TCombobox', fieldbackground=[('readonly', ModernColors.DARK_BG)])
        style.configure('TEntry', background=ModernColors.DARK_BG, fieldbackground=ModernColors.DARK_BG, foreground=ModernColors.TEXT_PRIMARY)
        style.configure('Horizontal.TProgressbar', background=ModernColors.ACCENT)
        style.configure('Modern.TCombobox', fieldbackground=ModernColors.DARK_BG)
        style.configure('Modern.TEntry', fieldbackground=ModernColors.DARK_BG)
        style.configure('Modern.Horizontal.TScale', background=ModernColors.DARKER_BG)
    
    def setup_ui(self):
        """Setup the main UI components with resizable layout"""
        # Create main container
        main_container = tk.Frame(self.root, bg=ModernColors.DARK_BG)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create UI components
        self.toolbar = Toolbar(main_container, self)
        self.sidebar = Sidebar(main_container, self)
        self.canvas_area = CanvasArea(main_container, self)
        self.control_panel = ControlPanel(main_container, self)
        
        # Create status bar
        self.create_status_bar(self.root)
    
    def create_status_bar(self, parent):
        """Create bottom status bar"""
        status_frame = tk.Frame(parent, bg=ModernColors.DARKER_BG, height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(status_frame, 
                                  text="Ready", 
                                  bg=ModernColors.DARKER_BG, 
                                  fg=ModernColors.TEXT_SECONDARY,
                                  anchor="w", padx=10, pady=2)
        self.status_bar.pack(fill=tk.X)
    
    def connect_events(self):
        """Connect event handlers"""
        # File menu events
        # Other event connections
        pass
    
    # ---- File Operations ----
    
    def open_folder(self):
        """Open a folder of images"""
        folder_path = filedialog.askdirectory(title="Select Images Folder")
        if not folder_path:
            return
        
        # Show progress
        self.toolbar.show_progress()
        self.update_status("Loading images...")
        
        # Run in background thread to keep UI responsive
        def load_thread():
            # Load images
            success = self.image_manager.load_images_from_folder(folder_path)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._on_images_loaded(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _on_images_loaded(self, success):
        """Handle completion of image loading"""
        self.toolbar.hide_progress()
        
        if success and self.image_manager.image_files:
            # Load annotations
            self.annotation_manager.load_annotations(
                os.path.join(self.image_manager.images_folder, "annotations"),
                self.image_manager.image_files
            )
            
            # Start thumbnail loading
            self.image_manager.start_thumbnail_loading()
            
            # Load first image
            self.load_current_image()
            
            # Update status
            self.update_status(f"Loaded {len(self.image_manager.image_files)} images from folder")
        else:
            messagebox.showwarning("No Images", "No supported image files found in the selected folder.\n\nSupported formats: JPG, PNG, BMP, TIFF, GIF, WebP")
    
    def save_annotations(self):
        """Save annotations to JSON files"""
        if not self.image_manager.images_folder:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        # Update annotations for current image before saving
        self.update_annotations()
        
        # Save all annotations
        annotations_folder = os.path.join(self.image_manager.images_folder, "annotations")
        self.annotation_manager.save_annotations(annotations_folder)
        
        # Update status
        self.update_status(f"Saved annotations to {annotations_folder}")
    
    # ---- Image Navigation ----
    
    def load_current_image(self):
        """Load and display the current image"""
        # Get current image path
        image_path = self.image_manager.get_current_image_path()
        if not image_path:
            return
        
        # Load image
        image = self.image_manager.load_current_image()
        if not image:
            return
        
        # Display image
        self.canvas_area.display_image(image)
        
        # Get current image name
        current_image_name = self.image_manager.image_files[self.image_manager.current_image_index]
        
        # Update image info in controls panel
        self.control_panel.update_image_info(
            current_image_name, 
            self.image_manager.current_image.width, 
            self.image_manager.current_image.height
        )
        
        # Update status
        self.update_status(f"Loaded image {self.image_manager.current_image_index + 1} of {len(self.image_manager.image_files)}: {current_image_name}")
        
        # Redraw annotations
        self.redraw_annotations()
        
        # Update statistics
        self.update_statistics()
    
    def next_image(self):
        """Navigate to next image"""
        if self.image_manager.next_image():
            # Save current annotations before moving
            self.update_annotations()
            self.load_current_image()
            return True
        return False
    
    def previous_image(self):
        """Navigate to previous image"""
        if self.image_manager.previous_image():
            # Save current annotations before moving
            self.update_annotations()
            self.load_current_image()
            return True
        return False
    
    def jump_to_image(self, index):
        """Jump directly to an image by its index"""
        if self.image_manager.jump_to_image(index):
            # Save current annotations before jumping
            self.update_annotations()
            self.load_current_image()
            return True
        return False
    
    def jump_to_image_by_number(self, image_number):
        """Jump to a specific image by its number"""
        if not self.image_manager.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return False
        
        # Check if the number is valid
        if image_number < 1 or image_number > len(self.image_manager.image_files):
            messagebox.showwarning("Invalid Number", 
                                 f"Please enter a number between 1 and {len(self.image_manager.image_files)}")
            return False
        
        # Adjust for 0-based indexing
        target_index = image_number - 1
        
        # Jump to the image
        result = self.jump_to_image(target_index)
        if result:
            self.update_status(f"Navigated to image {image_number} of {len(self.image_manager.image_files)}")
        
        return result
    
    # ---- Annotation Operations ----
    
    def update_annotations(self):
        """Update annotations for current image"""
        if not self.image_manager.image_files:
            return
        
        current_image_name = self.image_manager.image_files[self.image_manager.current_image_index]
        
        # Save undo state before updating
        if current_image_name in self.annotation_manager.annotations:
            self.undo_manager.save_state({
                'image': current_image_name,
                'annotations': self.annotation_manager.annotations.get(current_image_name, [])
            })
    
    def redraw_annotations(self):
        """Redraw annotations on canvas"""
        if not self.image_manager.image_files or not self.boxes_visible:
            return
        
        current_image_name = self.image_manager.image_files[self.image_manager.current_image_index]
        annotations = self.annotation_manager.get_annotations(current_image_name)
        
        self.canvas_area.redraw_annotations(annotations, self.selected_annotation_id)
    
    def toggle_boxes_visibility(self):
        """Toggle the visibility of annotation boxes"""
        self.boxes_visible = not self.boxes_visible
        
        if self.boxes_visible:
            # Show boxes
            self.redraw_annotations()
            self.update_status("👁️ Bounding boxes are now visible")
            self.sidebar.update_visibility_button(True)
        else:
            # Hide boxes
            self.canvas_area.canvas.delete('annotation')
            self.canvas_area.canvas.delete('selected')
            self.update_status("👂 Bounding boxes are now hidden")
            self.sidebar.update_visibility_button(False)
    
    def complete_current_annotation(self):
        """Mark current image as completely annotated"""
        if not self.image_manager.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        current_image_name = self.image_manager.image_files[self.image_manager.current_image_index]
        
        # First make sure annotations are updated
        self.update_annotations()
        
        # Mark as annotated
        if current_image_name in self.annotation_manager.annotations and len(self.annotation_manager.annotations[current_image_name]) > 0:
            self.annotation_manager.mark_as_annotated(current_image_name)
            self.update_status(f"✅ Image {current_image_name} marked as completely annotated")
            
            # Update the annotated images tab with this image
            self.update_annotated_thumbnails()
            
            # Move to next image if available
            if self.image_manager.current_image_index < len(self.image_manager.image_files) - 1:
                self.next_image()
        else:
            messagebox.showwarning("No Annotations", "Please add at least one annotation before completing.")
    
    def update_annotated_thumbnails(self):
        """Update the annotated images thumbnails"""
        annotated_files = self.annotation_manager.get_annotated_images()
        self.sidebar.update_annotated_thumbnails(
            annotated_files,
            self.image_manager.images_folder,
            self.image_manager.thumbnail_cache,
            self.annotation_manager.annotations
        )
    
    # ---- Canvas Interaction Handlers ----
    
    def on_canvas_click(self, x, y):
        """Handle mouse click on canvas"""
        # Implementation for drawing or editing annotations
        pass
    
    def on_canvas_drag(self, x, y):
        """Handle mouse drag on canvas"""
        # Implementation for drawing or editing annotations
        pass
    
    def on_canvas_release(self, x, y):
        """Handle mouse release on canvas"""
        # Implementation for drawing or editing annotations
        pass
    
    def on_mouse_motion(self, x, y):
        """Handle mouse motion over canvas"""
        # Implementation for cursor changes
        pass
    
    def on_double_click(self, x, y):
        """Handle double click on canvas"""
        # Implementation for editing class
        pass
    
    # ---- Utility Methods ----
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.configure(text=message)
    
    def update_statistics(self):
        """Update annotation statistics"""
        total_annotations = sum(len(anns) for anns in self.annotation_manager.annotations.values())
        annotated_images_count = len(self.annotation_manager.annotated_images)
        
        self.control_panel.update_statistics(total_annotations, annotated_images_count)
    
    def load_more_thumbnails(self):
        """Load more thumbnails"""
        if self.image_manager.load_more_thumbnails():
            # Update thumbnail display
            pass
    
    def run_model(self):
        """Run AI model on current image"""
        # Implementation for running AI model
        pass
    
    def set_mode(self, mode):
        """Set drawing or editing mode"""
        if mode == 'draw':
            self.drawing = True
            self.editing = False
        elif mode == 'edit':
            self.drawing = False
            self.editing = True
        
        # Update UI to reflect mode
        self.toolbar.update_tool_buttons(mode)
    
    def cleanup(self):
        """Clean up resources before closing"""
        self.image_manager.cleanup()
