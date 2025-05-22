import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import math

from .styles import ModernColors

class CanvasArea:
    """Enhanced canvas area with annotation capabilities"""
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app = app_controller
        
        # Create canvas container frame
        self.canvas_frame = tk.Frame(parent, bg=ModernColors.DARK_BG)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Canvas area with scrollbars
        self.create_scrollable_canvas()
        
        # Drawing and editing state
        self.drawing = False
        self.editing = False
        self.selected_annotation_id = None
        self.selected_handle = None
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        
        # Zoom state
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Setup bindings
        self.setup_bindings()
    
    def create_scrollable_canvas(self):
        """Create scrollable canvas for image display and annotations"""
        # Canvas container with scrollbars
        canvas_container = tk.Frame(self.canvas_frame, bg=ModernColors.DARK_BG)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_container, 
                             bg=ModernColors.CANVAS_BG,
                             xscrollcommand=h_scrollbar.set,
                             yscrollcommand=v_scrollbar.set,
                             highlightthickness=0,
                             bd=0)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Place canvas and scrollbars
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status overlay for zoom level
        self.zoom_status = tk.Label(self.canvas, text="Zoom: 100%",
                                 bg='#00000080', fg='white',
                                 font=('Segoe UI', 9))
    
    def setup_bindings(self):
        """Setup mouse and keyboard bindings for the canvas"""
        # Mouse bindings for drawing and editing
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # Mouse wheel for zooming
        self.canvas.bind("<Control-MouseWheel>", self.on_mousewheel_zoom)
        
        # Pan with middle mouse button
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_move)
    
    def display_image(self, image):
        """Display the current image on the canvas"""
        if not image:
            return
        
        # Calculate scaled dimensions based on zoom level
        width = int(image.width * self.zoom_level)
        height = int(image.height * self.zoom_level)
        
        # Resize image for display
        if self.zoom_level == 1.0:
            # No resizing needed at 100% zoom
            resized_img = image
        else:
            # Resize the image
            resized_img = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for display
        self.photo_image = ImageTk.PhotoImage(resized_img)
        
        # Clear canvas and display new image
        self.canvas.delete("all")
        self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)
        
        # Update canvas scroll region
        self.canvas.config(scrollregion=(0, 0, width, height))
        
        # Show zoom status
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_status.config(text=f"Zoom: {zoom_percent}%")
        self.zoom_status_id = self.canvas.create_window(10, 10, anchor="nw", window=self.zoom_status)
        
        # Hide zoom status after 2 seconds
        self.canvas.after(2000, lambda: self.canvas.delete(self.zoom_status_id) if hasattr(self, 'zoom_status_id') else None)
    
    def on_canvas_click(self, event):
        """Handle mouse click on canvas"""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # Delegate to app controller
        self.app.on_canvas_click(self.start_x, self.start_y)
    
    def on_canvas_drag(self, event):
        """Handle mouse drag on canvas"""
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # Delegate to app controller
        self.app.on_canvas_drag(self.current_x, self.current_y)
    
    def on_canvas_release(self, event):
        """Handle mouse release on canvas"""
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # Delegate to app controller
        self.app.on_canvas_release(self.current_x, self.current_y)
    
    def on_mouse_motion(self, event):
        """Handle mouse motion over canvas (for cursor changes)"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Delegate to app controller
        self.app.on_mouse_motion(x, y)
    
    def on_double_click(self, event):
        """Handle double click on canvas (for editing class)"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Delegate to app controller
        self.app.on_double_click(x, y)
    
    def on_mousewheel_zoom(self, event):
        """Handle mouse wheel zoom"""
        # Calculate new zoom level
        zoom_factor = 0.1 if event.delta > 0 else -0.1
        new_zoom = self.zoom_level + zoom_factor
        
        # Clamp zoom level
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # Apply zoom if changed
        if new_zoom != self.zoom_level:
            # Remember scroll position
            x_scroll = self.canvas.canvasx(event.x)
            y_scroll = self.canvas.canvasy(event.y)
            
            # Calculate relative position
            rel_x = x_scroll / (self.canvas.winfo_width() * self.zoom_level)
            rel_y = y_scroll / (self.canvas.winfo_height() * self.zoom_level)
            
            # Apply new zoom
            self.zoom_level = new_zoom
            
            # Reload the image with new zoom
            self.app.reload_current_image()
            
            # Restore scroll position
            self.canvas.xview_moveto(rel_x - (event.x / self.canvas.winfo_width()))
            self.canvas.yview_moveto(rel_y - (event.y / self.canvas.winfo_height()))
    
    def on_pan_start(self, event):
        """Start panning the canvas"""
        self.canvas.config(cursor="hand2")
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def on_pan_move(self, event):
        """Pan the canvas"""
        # Calculate how far we've moved
        dx = self.pan_start_x - event.x
        dy = self.pan_start_y - event.y
        
        # Scroll the canvas
        self.canvas.xview_scroll(int(dx), "units")
        self.canvas.yview_scroll(int(dy), "units")
        
        # Save new position
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def draw_temp_annotation(self, x1, y1, x2, y2):
        """Draw temporary annotation box while drawing"""
        self.canvas.delete("temp_box")
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=ModernColors.ACCENT,
            width=2,
            tags="temp_box"
        )
    
    def draw_annotation(self, annotation, selected=False, is_model_annotation=False):
        """Draw a single annotation box"""
        if 'bbox' not in annotation:
            return
        
        # Extract coordinates and apply zoom
        x1, y1, x2, y2 = [coord * self.zoom_level for coord in annotation['bbox']]
        
        # Get color
        color = annotation.get('color', ModernColors.ACCENT)
        if is_model_annotation:
            color = ModernColors.MODEL_ANNOTATION
        
        # Get class label
        class_name = annotation.get('class', 'unknown')
        
        # Create rectangle
        tag_id = f"annotation_{annotation.get('id', 'unknown')}"
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=color,
            width=2,
            tags=("annotation", tag_id)
        )
        
        # Add label background
        label_bg_id = self.canvas.create_rectangle(
            x1, y1 - 20, x1 + len(class_name) * 7 + 10, y1,
            fill=color,
            outline=color,
            tags=("annotation", tag_id)
        )
        
        # Add class label
        label_id = self.canvas.create_text(
            x1 + 5, y1 - 10,
            text=class_name,
            fill="white",
            anchor="w",
            font=("Segoe UI", 9),
            tags=("annotation", tag_id)
        )
        
        # If model annotation, add confidence
        if 'confidence' in annotation:
            conf_str = f"{annotation['confidence']:.2f}"
            conf_bg_id = self.canvas.create_rectangle(
                x2 - len(conf_str) * 7 - 10, y1 - 20, x2, y1,
                fill=color,
                outline=color,
                tags=("annotation", tag_id)
            )
            conf_id = self.canvas.create_text(
                x2 - 5, y1 - 10,
                text=conf_str,
                fill="white",
                anchor="e",
                font=("Segoe UI", 9),
                tags=("annotation", tag_id)
            )
        
        # If selected, add handles for resizing
        if selected:
            self.add_selection_handles(x1, y1, x2, y2, tag_id)
    
    def add_selection_handles(self, x1, y1, x2, y2, tag_id):
        """Add selection handles to a selected annotation"""
        handle_size = 6
        handle_color = ModernColors.HANDLE_COLOR
        
        # Corner handles
        self.canvas.create_rectangle(
            x1 - handle_size, y1 - handle_size, x1 + handle_size, y1 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_tl", "handle")
        )
        self.canvas.create_rectangle(
            x2 - handle_size, y1 - handle_size, x2 + handle_size, y1 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_tr", "handle")
        )
        self.canvas.create_rectangle(
            x1 - handle_size, y2 - handle_size, x1 + handle_size, y2 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_bl", "handle")
        )
        self.canvas.create_rectangle(
            x2 - handle_size, y2 - handle_size, x2 + handle_size, y2 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_br", "handle")
        )
        
        # Edge handles
        self.canvas.create_rectangle(
            (x1 + x2) / 2 - handle_size, y1 - handle_size, (x1 + x2) / 2 + handle_size, y1 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_t", "handle")
        )
        self.canvas.create_rectangle(
            (x1 + x2) / 2 - handle_size, y2 - handle_size, (x1 + x2) / 2 + handle_size, y2 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_b", "handle")
        )
        self.canvas.create_rectangle(
            x1 - handle_size, (y1 + y2) / 2 - handle_size, x1 + handle_size, (y1 + y2) / 2 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_l", "handle")
        )
        self.canvas.create_rectangle(
            x2 - handle_size, (y1 + y2) / 2 - handle_size, x2 + handle_size, (y1 + y2) / 2 + handle_size,
            fill=handle_color, outline="black", tags=("selected", f"{tag_id}_handle_r", "handle")
        )
    
    def redraw_annotations(self, annotations, selected_id=None):
        """Redraw all annotations"""
        # Clear existing annotations
        self.canvas.delete("annotation")
        self.canvas.delete("selected")
        
        # Draw each annotation
        for annotation in annotations:
            is_selected = annotation.get('id', None) == selected_id
            is_model = annotation.get('is_model_annotation', False)
            self.draw_annotation(annotation, is_selected, is_model)
    
    def set_cursor(self, cursor_type):
        """Set the canvas cursor"""
        self.canvas.config(cursor=cursor_type)
    
    def reset_zoom(self):
        """Reset zoom level to 100%"""
        self.zoom_level = 1.0
        self.app.reload_current_image()
