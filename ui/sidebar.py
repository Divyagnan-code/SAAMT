import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

from .styles import ModernColors, ModernButton

class Sidebar:
    """Enhanced left sidebar with image thumbnails and navigation controls"""
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app = app_controller
        
        # Create sidebar frame
        self.sidebar_frame = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG, width=250)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)  # Don't shrink
        
        # Build UI components
        self.create_header()
        self.create_controls()
        self.create_notebook()
    
    def create_header(self):
        """Create sidebar header"""
        header_frame = tk.Frame(self.sidebar_frame, bg=ModernColors.SIDEBAR_BG)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(header_frame, text="📷 Images", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
    
    def create_controls(self):
        """Create navigation and control buttons"""
        controls_frame = tk.Frame(self.sidebar_frame, bg=ModernColors.SIDEBAR_BG)
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Jump to image controls
        jump_frame = tk.Frame(controls_frame, bg=ModernColors.SIDEBAR_BG)
        jump_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(jump_frame, text="Go to image:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.jump_entry = ttk.Entry(jump_frame, width=6, style='Modern.TEntry')
        self.jump_entry.pack(side=tk.LEFT)
        
        jump_btn = ModernButton(jump_frame, text="Go", 
                               command=self.jump_to_image_by_number, 
                               font=('Segoe UI', 8), padx=8, pady=2)
        jump_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Navigation buttons
        nav_buttons = tk.Frame(controls_frame, bg=ModernColors.SIDEBAR_BG)
        nav_buttons.pack(fill=tk.X, pady=(0, 5))
        
        prev_btn = ModernButton(nav_buttons, text="◀ Previous", 
                              command=self.app.previous_image, 
                              font=('Segoe UI', 9), padx=10, pady=4)
        prev_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        next_btn = ModernButton(nav_buttons, text="Next ▶", 
                              command=self.app.next_image, 
                              font=('Segoe UI', 9), padx=10, pady=4)
        next_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Visibility and annotation controls
        control_actions = tk.Frame(controls_frame, bg=ModernColors.SIDEBAR_BG)
        control_actions.pack(fill=tk.X, pady=(0, 5))
        
        # Visibility toggle button
        self.visibility_btn = ModernButton(control_actions, text="👁️ Hide Boxes", 
                                      command=self.app.toggle_boxes_visibility, 
                                      font=('Segoe UI', 9), padx=10, pady=4)
        self.visibility_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Complete annotation button
        self.complete_btn = ModernButton(control_actions, text="✓ Complete Annotation", 
                                    command=self.app.complete_current_annotation, 
                                    bg=ModernColors.BUTTON_SUCCESS, 
                                    hover_color='#12a530',
                                    font=('Segoe UI', 9, 'bold'), padx=10, pady=4)
        self.complete_btn.pack(fill=tk.X)
    
    def create_notebook(self):
        """Create tabbed notebook for all images and annotated images"""
        # Create notebook for tabs
        self.sidebar_notebook = ttk.Notebook(self.sidebar_frame)
        self.sidebar_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: All Images
        self.all_images_frame = tk.Frame(self.sidebar_notebook, bg=ModernColors.SIDEBAR_BG)
        self.sidebar_notebook.add(self.all_images_frame, text="All Images")
        
        # Tab 2: Annotated Images
        self.annotated_images_frame = tk.Frame(self.sidebar_notebook, bg=ModernColors.SIDEBAR_BG)
        self.sidebar_notebook.add(self.annotated_images_frame, text="Annotated Images")
        
        # Setup "All Images" tab content
        self.setup_all_images_tab()
        
        # Setup "Annotated Images" tab content
        self.setup_annotated_images_tab()
    
    def setup_all_images_tab(self):
        """Setup the All Images tab content"""
        all_header = tk.Frame(self.all_images_frame, bg=ModernColors.SIDEBAR_BG)
        all_header.pack(fill=tk.X, padx=5, pady=5)
        
        # Load more button for all images
        self.load_more_btn = ModernButton(all_header, text="Load More", 
                                      command=self.app.load_more_thumbnails, 
                                      bg=ModernColors.BUTTON_SECONDARY,
                                      font=('Segoe UI', 8), padx=5, pady=2)
        self.load_more_btn.pack(side=tk.RIGHT)
        self.load_more_btn.pack_forget()  # Will be shown when needed
        
        # Container for all images thumbnails
        all_thumb_container = tk.Frame(self.all_images_frame, bg=ModernColors.SIDEBAR_BG)
        all_thumb_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame with vertical scrolling for all images
        self.thumb_canvas = tk.Canvas(all_thumb_container, bg=ModernColors.SIDEBAR_BG, 
                                     highlightthickness=0, bd=0)
        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar for all images
        v_scrollbar_all = ttk.Scrollbar(all_thumb_container, orient="vertical", 
                                      command=self.thumb_canvas.yview)
        v_scrollbar_all.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.thumb_scrollable_frame = tk.Frame(self.thumb_canvas, bg=ModernColors.SIDEBAR_BG)
        self.thumb_canvas_window = self.thumb_canvas.create_window((0, 0), 
                                                                 window=self.thumb_scrollable_frame, 
                                                                 anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=v_scrollbar_all.set)
        
        # Configure scrolling for all images
        self.thumb_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        )
    
    def setup_annotated_images_tab(self):
        """Setup the Annotated Images tab content"""
        ann_header = tk.Frame(self.annotated_images_frame, bg=ModernColors.SIDEBAR_BG)
        ann_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(ann_header, text="Completed Annotations", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        # Container for annotated images thumbnails
        ann_thumb_container = tk.Frame(self.annotated_images_frame, bg=ModernColors.SIDEBAR_BG)
        ann_thumb_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame for annotated images
        self.annotated_thumb_canvas = tk.Canvas(ann_thumb_container, bg=ModernColors.SIDEBAR_BG, 
                                              highlightthickness=0, bd=0)
        self.annotated_thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar for annotated images
        v_scrollbar_ann = ttk.Scrollbar(ann_thumb_container, orient="vertical", 
                                       command=self.annotated_thumb_canvas.yview)
        v_scrollbar_ann.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.annotated_thumb_scrollable_frame = tk.Frame(self.annotated_thumb_canvas, bg=ModernColors.SIDEBAR_BG)
        self.annotated_thumb_window = self.annotated_thumb_canvas.create_window((0, 0), 
                                                                            window=self.annotated_thumb_scrollable_frame, 
                                                                            anchor="nw")
        self.annotated_thumb_canvas.configure(yscrollcommand=v_scrollbar_ann.set)
        
        # Configure scrolling for annotated images
        self.annotated_thumb_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.annotated_thumb_canvas.configure(scrollregion=self.annotated_thumb_canvas.bbox("all"))
        )
        
        # Bind mousewheel event for both tabs
        self.setup_mousewheel_scrolling()
    
    def setup_mousewheel_scrolling(self):
        """Set up mousewheel scrolling for both tabs"""
        def _on_mousewheel(event):
            # Determine which tab is active
            current_tab = self.sidebar_notebook.index("current")
            if current_tab == 0:  # All Images tab
                self.thumb_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:  # Annotated Images tab
                self.annotated_thumb_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mousewheel event to all relevant widgets
        for widget in [self.thumb_canvas, self.thumb_scrollable_frame, 
                      self.annotated_thumb_canvas, self.annotated_thumb_scrollable_frame]:
            widget.bind("<MouseWheel>", _on_mousewheel)
    
    def jump_to_image_by_number(self):
        """Jump to a specific image by its number"""
        try:
            # Get the number from the entry field
            image_number = int(self.jump_entry.get())
            
            # Let the controller handle the actual navigation
            result = self.app.jump_to_image_by_number(image_number)
            
            # Clear the entry field
            self.jump_entry.delete(0, tk.END)
            
            return result
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number.")
            return False
    
    def update_load_more_button(self, show=False):
        """Update the visibility of the Load More button"""
        if show:
            self.load_more_btn.pack(side=tk.RIGHT)
        else:
            self.load_more_btn.pack_forget()
    
    def update_thumbnails(self, image_files, images_folder, thumbnail_cache):
        """Update the All Images thumbnails"""
        # Clear existing thumbnails
        for widget in self.thumb_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not image_files:
            msg_label = tk.Label(self.thumb_scrollable_frame, 
                               text="No images loaded", 
                               bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                               font=('Segoe UI', 10))
            msg_label.pack(pady=20)
            return
        
        # Create thumbnails for the current batch
        for i, image_file in enumerate(image_files):
            if i < len(thumbnail_cache):
                self.create_thumbnail(i, image_file, thumbnail_cache[i], self.thumb_scrollable_frame)
    
    def update_annotated_thumbnails(self, annotated_files, images_folder, thumbnail_cache, annotations):
        """Update the Annotated Images thumbnails"""
        # Clear existing thumbnails
        for widget in self.annotated_thumb_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not annotated_files:
            # Show a message if no annotated images
            msg_label = tk.Label(self.annotated_thumb_scrollable_frame, 
                               text="No completed annotations yet", 
                               bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                               font=('Segoe UI', 10))
            msg_label.pack(pady=20)
            return
        
        # Create thumbnails for annotated images
        for i, image_file in enumerate(annotated_files):
            idx = image_files.index(image_file)
            if idx in thumbnail_cache:
                self.create_annotated_thumbnail(
                    idx, image_file, thumbnail_cache[idx],
                    self.annotated_thumb_scrollable_frame,
                    len(annotations.get(image_file, []))
                )
    
    def create_thumbnail(self, idx, image_file, photo, parent_frame):
        """Create a thumbnail widget for the image"""
        try:
            # Create thumbnail frame
            thumb_frame = tk.Frame(parent_frame, bg=ModernColors.SIDEBAR_BG, 
                                  relief=tk.SOLID, bd=1)
            thumb_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Thumbnail button
            thumb_btn = tk.Button(thumb_frame, image=photo, 
                                 bg=ModernColors.SIDEBAR_BG, bd=0, relief=tk.FLAT,
                                 cursor='hand2',
                                 command=lambda idx=idx: self.app.jump_to_image(idx))
            thumb_btn.image = photo  # Keep reference
            thumb_btn.pack(pady=2)
            
            # Image name
            name_label = tk.Label(thumb_frame, 
                                 text=f"{idx+1}. {image_file[:18]}{'...' if len(image_file) > 18 else ''}",
                                 bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                 font=('Segoe UI', 8), wraplength=180, justify=tk.LEFT)
            name_label.pack(anchor=tk.W, padx=5, pady=(0, 3))
            
            # Hover effects
            self.add_hover_effects(thumb_frame, [thumb_btn, name_label])
            
        except Exception as e:
            print(f"Error creating thumbnail for {image_file}: {e}")
    
    def create_annotated_thumbnail(self, idx, image_file, photo, parent_frame, annotation_count):
        """Create a thumbnail widget for an annotated image"""
        try:
            # Create thumbnail frame
            thumb_frame = tk.Frame(parent_frame, bg=ModernColors.SIDEBAR_BG, 
                                  relief=tk.SOLID, bd=1)
            thumb_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Thumbnail button
            thumb_btn = tk.Button(thumb_frame, image=photo, 
                                 bg=ModernColors.SIDEBAR_BG, bd=0, relief=tk.FLAT,
                                 cursor='hand2',
                                 command=lambda idx=idx: self.app.jump_to_image(idx))
            thumb_btn.image = photo  # Keep reference
            thumb_btn.pack(pady=2)
            
            # Image name and status
            info_frame = tk.Frame(thumb_frame, bg=ModernColors.SIDEBAR_BG)
            info_frame.pack(fill=tk.X, padx=5)
            
            name_label = tk.Label(info_frame, 
                                 text=f"{idx+1}. {image_file[:18]}{'...' if len(image_file) > 18 else ''}",
                                 bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                 font=('Segoe UI', 8), wraplength=180, justify=tk.LEFT)
            name_label.pack(anchor=tk.W)
            
            # Annotation count
            status_text = f"📝 {annotation_count} annotations"
            status_label = tk.Label(info_frame, text=status_text,
                                   bg=ModernColors.SIDEBAR_BG, 
                                   fg=ModernColors.ACCENT,
                                   font=('Segoe UI', 7))
            status_label.pack(anchor=tk.W, pady=(0, 3))
            
            # Hover effects
            self.add_hover_effects(thumb_frame, [thumb_btn, name_label, status_label, info_frame])
            
        except Exception as e:
            print(f"Error creating annotated thumbnail for {image_file}: {e}")
    
    def add_hover_effects(self, frame, widgets):
        """Add hover effects to a frame and its widgets"""
        def on_enter(e, frame=frame):
            frame.configure(bg=ModernColors.ACCENT, relief=tk.SOLID)
            for w in widgets:
                if isinstance(w, tk.Frame):
                    w.configure(bg=ModernColors.ACCENT)
        
        def on_leave(e, frame=frame):
            frame.configure(bg=ModernColors.SIDEBAR_BG, relief=tk.SOLID)
            for w in widgets:
                if isinstance(w, tk.Frame):
                    w.configure(bg=ModernColors.SIDEBAR_BG)
        
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        
        for widget in widgets:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
    
    def update_visibility_button(self, visible):
        """Update the text on the visibility toggle button"""
        if visible:
            self.visibility_btn.configure(text="👁️ Hide Boxes")
        else:
            self.visibility_btn.configure(text="👁️ Show Boxes")
