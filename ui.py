import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageFont
import os
import json
from typing import Dict, List, Tuple, Optional
import math
import threading
import queue
import time

class ModernColors:
    """Modern color scheme for the application"""
    DARK_BG = '#1e1e1e'
    DARKER_BG = '#252526'
    SIDEBAR_BG = '#2d2d30'
    BUTTON_PRIMARY = '#0e639c'
    BUTTON_PRIMARY_HOVER = '#1177bb'
    BUTTON_SECONDARY = '#5a5a5a'
    BUTTON_SUCCESS = '#0e7a0d'
    BUTTON_WARNING = '#ca5010'
    BUTTON_DANGER = '#d13438'
    TEXT_PRIMARY = '#ffffff'
    TEXT_SECONDARY = '#cccccc'
    BORDER = '#3c3c3c'
    ACCENT = '#007acc'
    CANVAS_BG = '#f5f5f5'

class ModernButton(tk.Button):
    """Custom modern-looking button"""
    def __init__(self, parent, **kwargs):
        # Extract custom parameters
        hover_color = kwargs.pop('hover_color', ModernColors.BUTTON_PRIMARY_HOVER)
        normal_color = kwargs.pop('bg', ModernColors.BUTTON_PRIMARY)
        
        # Set default styling
        default_style = {
            'bg': normal_color,
            'fg': ModernColors.TEXT_PRIMARY,
            'font': ('Segoe UI', 9),
            'relief': 'flat',
            'borderwidth': 0,
            'cursor': 'hand2',
            'activebackground': hover_color,
            'activeforeground': ModernColors.TEXT_PRIMARY
        }
        
        # Merge with provided kwargs
        default_style.update(kwargs)
        
        super().__init__(parent, **default_style)
        
        # Store colors for hover effects
        self.normal_color = normal_color
        self.hover_color = hover_color
        
        # Bind hover effects
        self.bind('<Enter>', lambda e: self.configure(bg=self.hover_color))
        self.bind('<Leave>', lambda e: self.configure(bg=self.normal_color))

class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Annotation Tool")
        self.root.geometry("1600x1000")
        self.root.configure(bg=ModernColors.DARK_BG)
        
        # Configure ttk styles
        self.setup_styles()
        
        # Data structures
        self.images_folder = ""
        self.image_files = []
        self.current_image_index = 0
        self.current_image = None
        self.photo_image = None  # PhotoImage for canvas display
        
        # Annotation data
        self.annotations = {}
        self.temp_annotations = []
        self.current_class = "person"
        self.annotation_colors = ['#ff4444', '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff']
        self.color_index = 0
        
        # Drawing state
        self.drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_rect = None
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.panning = False
        self.boxes_visible = True
        
        # Async loading state
        self.thumbnail_cache = {}
        self.thumbnail_queue = queue.Queue()
        self.loading_thumbnails = False
        self.thumbnail_batch_size = 10
        self.current_batch_start = 0
        
        self.setup_ui()
    
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Modern.TFrame', background=ModernColors.DARK_BG)
        style.configure('Sidebar.TFrame', background=ModernColors.SIDEBAR_BG)
        style.configure('Modern.TLabel', background=ModernColors.DARK_BG, foreground=ModernColors.TEXT_PRIMARY, font=('Segoe UI', 9))
        style.configure('Modern.TEntry', font=('Segoe UI', 9))
        style.configure('Modern.TCombobox', font=('Segoe UI', 9))
        style.configure('Modern.Horizontal.TProgressbar', background=ModernColors.ACCENT)
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Main container
        main_frame = tk.Frame(self.root, bg=ModernColors.DARK_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top toolbar
        self.create_toolbar(main_frame)
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg=ModernColors.DARK_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.create_sidebar(content_frame)
        self.create_canvas_area(content_frame)
        self.create_right_controls(content_frame)
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """Create top toolbar with main controls"""
        toolbar = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG, height=70)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        toolbar.pack_propagate(False)
        
        # Left section
        left_section = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        left_section.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=10)
        
        # Folder selection
        folder_btn = ModernButton(left_section, text="📁 Select Images Folder", 
                                 command=self.select_folder, font=('Segoe UI', 10, 'bold'),
                                 padx=20, pady=8)
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Mode selection
        mode_frame = tk.Frame(left_section, bg=ModernColors.SIDEBAR_BG)
        mode_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(mode_frame, text="Mode:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                font=('Segoe UI', 9)).pack(anchor=tk.W)
        self.annotation_mode = tk.StringVar(value="bounding_box")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.annotation_mode,
                                 values=["bounding_box", "instance_segmentation", "classification"],
                                 state="readonly", width=18, style='Modern.TCombobox')
        mode_combo.pack()
        
        # Progress section (center)
        self.progress_frame = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        self.progress_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        self.progress_label = tk.Label(self.progress_frame, text="", bg=ModernColors.SIDEBAR_BG, 
                                      fg=ModernColors.TEXT_SECONDARY, font=('Segoe UI', 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=250, mode='determinate',
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack()
        self.progress_frame.pack_forget()
        
        # Right section
        right_section = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        right_section.pack(side=tk.RIGHT, fill=tk.Y, padx=15, pady=10)
        
        # Action buttons
        try_btn = ModernButton(right_section, text="🧪 Try Model", 
                              command=self.try_model, bg=ModernColors.BUTTON_WARNING,
                              hover_color='#e86900', font=('Segoe UI', 10), padx=15, pady=8)
        try_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        train_btn = ModernButton(right_section, text="🚀 Train Model", 
                                command=self.train_model, bg=ModernColors.BUTTON_DANGER,
                                hover_color='#e74856', font=('Segoe UI', 10), padx=15, pady=8)
        train_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_sidebar(self, parent):
        """Create left sidebar with image thumbnails"""
        sidebar = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG, width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)
        
        # Header
        header_frame = tk.Frame(sidebar, bg=ModernColors.SIDEBAR_BG)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="📷 Images", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Load more button
        self.load_more_btn = ModernButton(header_frame, text="⬇️", 
                                         command=self.load_more_thumbnails, 
                                         bg=ModernColors.BUTTON_SECONDARY,
                                         font=('Segoe UI', 8), padx=8, pady=4)
        self.load_more_btn.pack(side=tk.RIGHT)
        self.load_more_btn.pack_forget()
        
        # Thumbnails container
        thumb_container = tk.Frame(sidebar, bg=ModernColors.SIDEBAR_BG)
        thumb_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 15))
        
        # Create scrollable frame
        self.thumb_canvas = tk.Canvas(thumb_container, bg=ModernColors.SIDEBAR_BG, 
                                     highlightthickness=0, bd=0)
        thumb_scrollbar = ttk.Scrollbar(thumb_container, orient="vertical", 
                                       command=self.thumb_canvas.yview)
        self.thumb_scrollable_frame = tk.Frame(self.thumb_canvas, bg=ModernColors.SIDEBAR_BG)
        
        # Configure scrolling
        self.thumb_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        )
        
        self.thumb_canvas_window = self.thumb_canvas.create_window((0, 0), window=self.thumb_scrollable_frame, anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=thumb_scrollbar.set)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.thumb_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.thumb_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.thumb_scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Update scroll region when canvas size changes
        def _configure_scroll_region(event):
            self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
            # Update the window width to match canvas width
            canvas_width = event.width
            self.thumb_canvas.itemconfig(self.thumb_canvas_window, width=canvas_width)
        
        self.thumb_canvas.bind('<Configure>', _configure_scroll_region)
        
        self.thumb_canvas.pack(side="left", fill="both", expand=True)
        thumb_scrollbar.pack(side="right", fill="y")
    
    def create_canvas_area(self, parent):
        """Create center canvas area for image display and annotation"""
        canvas_frame = tk.Frame(parent, bg=ModernColors.DARK_BG)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Canvas controls
        controls_frame = tk.Frame(canvas_frame, bg=ModernColors.DARKER_BG, height=60)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        controls_frame.pack_propagate(False)
        
        # Navigation section
        nav_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        nav_frame.pack(side=tk.LEFT, pady=12, padx=15)
        
        prev_btn = ModernButton(nav_frame, text="◀ Previous", command=self.previous_image,
                               bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=12, pady=6)
        prev_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        next_btn = ModernButton(nav_frame, text="Next ▶", command=self.next_image,
                               bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=12, pady=6)
        next_btn.pack(side=tk.LEFT)
        
        # Jump to image
        jump_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        jump_frame.pack(side=tk.LEFT, pady=12, padx=20)
        
        tk.Label(jump_frame, text="Go to:", bg=ModernColors.DARKER_BG, fg=ModernColors.TEXT_SECONDARY, 
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.jump_var = tk.StringVar()
        jump_entry = tk.Entry(jump_frame, textvariable=self.jump_var, width=8, 
                             font=('Segoe UI', 9), bg=ModernColors.CANVAS_BG, fg='#000000', bd=1)
        jump_entry.pack(side=tk.LEFT, padx=(0, 8))
        jump_entry.bind('<Return>', self.jump_to_image_by_number)
        
        jump_btn = ModernButton(jump_frame, text="Go", command=self.jump_to_image_by_number,
                               bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=10, pady=4)
        jump_btn.pack(side=tk.LEFT)
        
        # Zoom controls
        zoom_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        zoom_frame.pack(side=tk.LEFT, pady=12, padx=20)
        
        ModernButton(zoom_frame, text="🔍+", command=self.zoom_in,
                    bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
        ModernButton(zoom_frame, text="🔍-", command=self.zoom_out,
                    bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
        ModernButton(zoom_frame, text="⌂", command=self.reset_zoom,
                    bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
        
        # Visibility toggle
        toggle_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        toggle_frame.pack(side=tk.RIGHT, pady=12, padx=15)
        
        self.visibility_btn = ModernButton(toggle_frame, text="👁️ Hide Boxes", 
                                          command=self.toggle_boxes_visibility,
                                          bg='#6f42c1', hover_color='#8a63d2',
                                          font=('Segoe UI', 9), padx=12, pady=6)
        self.visibility_btn.pack()
        
        # Canvas container
        canvas_container = tk.Frame(canvas_frame, bg=ModernColors.BORDER, bd=1, relief=tk.SOLID)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, bg=ModernColors.CANVAS_BG, cursor="crosshair")
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.on_pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def create_right_controls(self, parent):
        """Create right sidebar with annotation controls"""
        right_panel = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG, width=280)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Class input section
        class_frame = tk.LabelFrame(right_panel, text=" 🏷️ Annotation Class ", 
                                   bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                   font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
        class_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        self.class_var = tk.StringVar(value=self.current_class)
        class_entry = tk.Entry(class_frame, textvariable=self.class_var, 
                              font=('Segoe UI', 11), bg=ModernColors.CANVAS_BG, fg='#000000', 
                              bd=1, relief=tk.SOLID)
        class_entry.pack(fill=tk.X, padx=10, pady=(10, 5))
        class_entry.bind('<Return>', self.update_current_class)
        
        ModernButton(class_frame, text="✓ Update Class", command=self.update_current_class,
                    bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                    font=('Segoe UI', 9), pady=6).pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Current annotations
        annotations_frame = tk.LabelFrame(right_panel, text=" 📝 Current Annotations ", 
                                         bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                         font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
        annotations_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Listbox container
        list_container = tk.Frame(annotations_frame, bg=ModernColors.SIDEBAR_BG)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.annotations_listbox = tk.Listbox(list_container, bg=ModernColors.CANVAS_BG, 
                                             fg='#000000', font=('Segoe UI', 9),
                                             selectbackground=ModernColors.ACCENT,
                                             bd=1, relief=tk.SOLID)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", 
                                      command=self.annotations_listbox.yview)
        self.annotations_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        self.annotations_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")
        
        # Annotation controls
        controls_container = tk.Frame(annotations_frame, bg=ModernColors.SIDEBAR_BG)
        controls_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ModernButton(controls_container, text="🎨 Change Color", 
                    command=self.change_annotation_color,
                    bg=ModernColors.BUTTON_WARNING, hover_color='#e86900',
                    font=('Segoe UI', 9), pady=5).pack(fill=tk.X, pady=2)
        
        ModernButton(controls_container, text="🗑️ Delete Selected", 
                    command=self.delete_selected_annotation,
                    bg=ModernColors.BUTTON_DANGER, hover_color='#e74856',
                    font=('Segoe UI', 9), pady=5).pack(fill=tk.X, pady=2)
        
        # Action buttons
        action_frame = tk.LabelFrame(right_panel, text=" ⚡ Actions ", 
                                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                    font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
        action_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        ModernButton(action_frame, text="💾 Update Annotations", command=self.update_annotations,
                    bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                    font=('Segoe UI', 10, 'bold'), pady=8).pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ModernButton(action_frame, text="👀 Preview Annotations", command=self.preview_annotations,
                    bg=ModernColors.BUTTON_PRIMARY, hover_color=ModernColors.BUTTON_PRIMARY_HOVER,
                    font=('Segoe UI', 10, 'bold'), pady=8).pack(fill=tk.X, padx=10, pady=(5, 10))
    
    def create_status_bar(self, parent):
        """Create bottom status bar"""
        status_frame = tk.Frame(parent, bg=ModernColors.DARKER_BG, height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        status_frame.pack_propagate(False)
        
        self.status_bar = tk.Label(status_frame, text="Ready - Select a folder to begin", 
                                  bg=ModernColors.DARKER_BG, fg=ModernColors.TEXT_SECONDARY, 
                                  font=('Segoe UI', 9), anchor=tk.W)
        self.status_bar.pack(fill=tk.BOTH, padx=15, pady=8)
    
    def select_folder(self):
        """Select folder containing images"""
        folder = filedialog.askdirectory(title="Select Images Folder")
        if folder:
            self.images_folder = folder
            self.load_images()
    
    def load_images(self):
        """Load image files from selected folder"""
        if not self.images_folder:
            return
        
        self.progress_frame.pack(side=tk.LEFT, padx=30, pady=15)
        self.progress_label.configure(text="Scanning folder...")
        self.progress_bar.configure(mode='indeterminate')
        self.progress_bar.start()
        
        threading.Thread(target=self._load_images_async, daemon=True).start()
    
    def _load_images_async(self):
        """Load images asynchronously"""
        try:
            supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp')
            self.image_files = []
            
            for file in os.listdir(self.images_folder):
                if file.lower().endswith(supported_formats):
                    # Check if file can be opened as image
                    try:
                        with Image.open(os.path.join(self.images_folder, file)) as test_img:
                            test_img.verify()
                        self.image_files.append(file)
                    except Exception as e:
                        print(f"Skipping invalid image file {file}: {e}")
            
            self.image_files.sort()
            self.root.after(0, self._on_images_loaded)
            
        except Exception as e:
            self.root.after(0, lambda: self._on_loading_error(str(e)))
    
    def _on_images_loaded(self):
        """Handle successful image loading"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        if self.image_files:
            self.current_image_index = 0
            self.current_batch_start = 0
            self.thumbnail_cache = {}
            
            self.load_existing_annotations()
            self.start_thumbnail_loading()
            self.load_current_image()
            
            self.update_status(f"Loaded {len(self.image_files)} images from folder")
        else:
            messagebox.showwarning("No Images", "No supported image files found in the selected folder.\n\nSupported formats: JPG, PNG, BMP, TIFF, GIF, WebP")
    
    def _on_loading_error(self, error_msg):
        """Handle loading error"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        messagebox.showerror("Error", f"Failed to load images: {error_msg}")
    
    def start_thumbnail_loading(self):
        """Start loading thumbnails"""
        if self.loading_thumbnails:
            return
            
        self.loading_thumbnails = True
        self.load_more_btn.pack(side=tk.RIGHT)
        
        # Clear existing thumbnails
        for widget in self.thumb_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.load_thumbnail_batch()
    
    def load_thumbnail_batch(self):
        """Load batch of thumbnails"""
        if not self.image_files or self.current_batch_start >= len(self.image_files):
            self.loading_thumbnails = False
            self.load_more_btn.pack_forget()
            return
        
        end_index = min(self.current_batch_start + self.thumbnail_batch_size, len(self.image_files))
        batch_files = self.image_files[self.current_batch_start:end_index]
        
        threading.Thread(target=self._load_thumbnails_async, 
                        args=(batch_files, self.current_batch_start), daemon=True).start()
    
    def _load_thumbnails_async(self, batch_files, start_index):
        """Load thumbnails asynchronously"""
        loaded_thumbnails = []
        
        for i, image_file in enumerate(batch_files):
            try:
                image_path = os.path.join(self.images_folder, image_file)
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Create thumbnail
                    img.thumbnail((160, 120), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    loaded_thumbnails.append({
                        'index': start_index + i,
                        'file': image_file,
                        'photo': photo
                    })
                    
            except Exception as e:
                print(f"Error creating thumbnail for {image_file}: {e}")
        
        self.root.after(0, lambda: self._on_thumbnails_loaded(loaded_thumbnails))
    
    def _on_thumbnails_loaded(self, loaded_thumbnails):
        """Handle loaded thumbnails"""
        for thumb_data in loaded_thumbnails:
            self.thumbnail_cache[thumb_data['index']] = thumb_data['photo']
            
            # Create thumbnail frame
            thumb_frame = tk.Frame(self.thumb_scrollable_frame, bg=ModernColors.SIDEBAR_BG, 
                                  relief=tk.SOLID, bd=1)
            thumb_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Thumbnail button
            thumb_btn = tk.Button(thumb_frame, image=thumb_data['photo'], 
                                 bg=ModernColors.SIDEBAR_BG, bd=0, relief=tk.FLAT,
                                 cursor='hand2',
                                 command=lambda idx=thumb_data['index']: self.jump_to_image(idx))
            thumb_btn.image = thumb_data['photo']  # Keep reference
            thumb_btn.pack(pady=2)
            
            # Image name label
            name_label = tk.Label(thumb_frame, 
                                 text=f"{thumb_data['index']+1}. {thumb_data['file'][:20]}{'...' if len(thumb_data['file']) > 20 else ''}",
                                 bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                 font=('Segoe UI', 8), wraplength=180)
            name_label.pack(pady=(0, 3))
            
            # Hover effects
            def on_enter(e, frame=thumb_frame):
                frame.configure(bg=ModernColors.ACCENT, relief=tk.SOLID)
            
            def on_leave(e, frame=thumb_frame):
                frame.configure(bg=ModernColors.SIDEBAR_BG, relief=tk.SOLID)
            
            thumb_frame.bind('<Enter>', on_enter)
            thumb_frame.bind('<Leave>', on_leave)
            thumb_btn.bind('<Enter>', on_enter)
            thumb_btn.bind('<Leave>', on_leave)
            name_label.bind('<Enter>', on_enter)
            name_label.bind('<Leave>', on_leave)
        
        self.current_batch_start += len(loaded_thumbnails)
        
        # Update scroll region
        self.thumb_canvas.update_idletasks()
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
    
    def load_more_thumbnails(self):
        """Load more thumbnails"""
        if not self.loading_thumbnails and self.current_batch_start < len(self.image_files):
            self.load_thumbnail_batch()
    
    def jump_to_image(self, index):
        """Jump to specific image"""
        if 0 <= index < len(self.image_files):
            self.current_image_index = index
            self.load_current_image()
    
    def jump_to_image_by_number(self, event=None):
        """Jump to image by number"""
        try:
            image_num = int(self.jump_var.get())
            if 1 <= image_num <= len(self.image_files):
                self.jump_to_image(image_num - 1)
                self.jump_var.set("")
            else:
                messagebox.showwarning("Invalid Image", f"Image number must be between 1 and {len(self.image_files)}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid image number")
    
    def load_current_image(self):
        """Load and display current image"""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return
        
        image_file = self.image_files[self.current_image_index]
        image_path = os.path.join(self.images_folder, image_file)
        
        try:
            # Close previous image to free memory
            if self.current_image:
                self.current_image.close()
            
            # Load new image
            self.current_image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if self.current_image.mode in ('RGBA', 'LA', 'P'):
                self.current_image = self.current_image.convert('RGB')
            
            self.reset_zoom()
            self.load_temp_annotations()
            self.update_status(f"Image {self.current_image_index + 1}/{len(self.image_files)}: {image_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.current_image = None
    
    def display_image_on_canvas(self):
        """Display image on canvas - FIXED METHOD NAME"""
        if not self.current_image:
            return
        
        try:
            # Calculate display size
            display_width = int(self.current_image.width * self.zoom_factor)
            display_height = int(self.current_image.height * self.zoom_factor)
            
            # Create resized image
            resized_image = self.current_image.resize((display_width, display_height), 
                                                     Image.Resampling.LANCZOS)
            
            # Clean up previous PhotoImage
            if self.photo_image:
                del self.photo_image
            
            # Create PhotoImage for canvas
            self.photo_image = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.photo_image)
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Draw annotations
            self.draw_annotations()
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            messagebox.showerror("Display Error", f"Failed to display image: {e}")
    
    def draw_annotations(self):
        """Draw annotations on canvas"""
        if not self.boxes_visible:
            return
        
        # Draw saved annotations
        current_image_name = self.image_files[self.current_image_index]
        if current_image_name in self.annotations:
            for ann in self.annotations[current_image_name]:
                if ann.get('visible', True):
                    self.draw_bbox(ann['bbox'], ann['color'], ann['class'])
        
        # Draw temporary annotations
        for ann in self.temp_annotations:
            if ann.get('visible', True):
                self.draw_bbox(ann['bbox'], ann['color'], ann['class'])
    
    def draw_bbox(self, bbox, color, class_name):
        """Draw bounding box on canvas"""
        x1, y1, x2, y2 = bbox
        
        # Scale coordinates
        x1 = x1 * self.zoom_factor + self.pan_x
        y1 = y1 * self.zoom_factor + self.pan_y
        x2 = x2 * self.zoom_factor + self.pan_x
        y2 = y2 * self.zoom_factor + self.pan_y
        
        # Draw rectangle
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3, tags="annotation")
        
        # Draw class label background
        text_bg = self.canvas.create_rectangle(x1-1, y1-20, x1+len(class_name)*8+10, y1, 
                                              fill=color, outline=color, tags="annotation")
        
        # Draw class label text
        self.canvas.create_text(x1+5, y1-10, text=class_name, fill='white', anchor=tk.W, 
                               font=('Segoe UI', 9, 'bold'), tags="annotation")
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        if self.annotation_mode.get() == "bounding_box":
            self.start_drawing(event)
    
    def start_drawing(self, event):
        """Start drawing bounding box"""
        self.drawing = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.drawing:
            self.draw_temp_bbox(event)
    
    def draw_temp_bbox(self, event):
        """Draw temporary bounding box"""
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        
        color = self.annotation_colors[self.color_index % len(self.annotation_colors)]
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, current_x, current_y,
            outline=color, width=3, tags="temp"
        )
    
    def on_canvas_release(self, event):
        """Handle canvas release"""
        if self.drawing:
            self.finish_drawing(event)
    
    def finish_drawing(self, event):
        """Finish drawing bounding box"""
        self.drawing = False
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
        
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        img_x1 = (self.start_x - self.pan_x) / self.zoom_factor
        img_y1 = (self.start_y - self.pan_y) / self.zoom_factor
        img_x2 = (end_x - self.pan_x) / self.zoom_factor
        img_y2 = (end_y - self.pan_y) / self.zoom_factor
        
        # Ensure proper order
        x1, x2 = min(img_x1, img_x2), max(img_x1, img_x2)
        y1, y2 = min(img_y1, img_y2), max(img_y1, img_y2)
        
        # Check minimum size
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            annotation = {
                'class': self.current_class,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'visible': True,
                'color': self.annotation_colors[self.color_index % len(self.annotation_colors)]
            }
            self.temp_annotations.append(annotation)
            self.color_index += 1
            self.display_image_on_canvas()  # Fixed method call
            self.update_annotations_list()
    
    def start_pan(self, event):
        """Start panning"""
        self.panning = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.canvas.configure(cursor="move")
    
    def on_pan(self, event):
        """Handle panning"""
        if self.panning:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.pan_x += dx
            self.pan_y += dy
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.display_image_on_canvas()  # Fixed method call
    
    def end_pan(self, event):
        """End panning"""
        self.panning = False
        self.canvas.configure(cursor="crosshair")
    
    def on_mousewheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """Zoom in"""
        if self.zoom_factor < 5.0:
            self.zoom_factor *= 1.2
            self.display_image_on_canvas()  # Fixed method call
    
    def zoom_out(self):
        """Zoom out"""
        if self.zoom_factor > 0.1:
            self.zoom_factor /= 1.2
            self.display_image_on_canvas()  # Fixed method call
    
    def reset_zoom(self):
        """Reset zoom and pan"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_image_on_canvas()  # Fixed method call
    
    def toggle_boxes_visibility(self):
        """Toggle bounding box visibility"""
        self.boxes_visible = not self.boxes_visible
        self.visibility_btn.configure(text="👁️ Show Boxes" if not self.boxes_visible else "👁️ Hide Boxes")
        self.display_image_on_canvas()  # Fixed method call
    
    def update_current_class(self, event=None):
        """Update current class"""
        new_class = self.class_var.get().strip()
        if new_class:
            self.current_class = new_class
            self.update_status(f"Current class: {self.current_class}")
    
    def load_temp_annotations(self):
        """Load temporary annotations for current image"""
        self.temp_annotations = []
        current_image_name = self.image_files[self.current_image_index]
        if current_image_name in self.annotations:
            for ann in self.annotations[current_image_name]:
                self.temp_annotations.append(ann.copy())
        self.update_annotations_list()
    
    def update_annotations_list(self):
        """Update annotations listbox"""
        self.annotations_listbox.delete(0, tk.END)
        for i, ann in enumerate(self.temp_annotations):
            status = "👁️" if ann.get('visible', True) else "🔒"
            bbox_str = f"[{ann['bbox'][0]},{ann['bbox'][1]},{ann['bbox'][2]},{ann['bbox'][3]}]"
            self.annotations_listbox.insert(tk.END, f"{status} {ann['class']}: {bbox_str}")
    
    def change_annotation_color(self):
        """Change annotation color"""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.temp_annotations):
                color = colorchooser.askcolor(title="Choose annotation color")[1]
                if color:
                    self.temp_annotations[idx]['color'] = color
                    self.display_image_on_canvas()  # Fixed method call
    
    def delete_selected_annotation(self):
        """Delete selected annotation"""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.temp_annotations):
                del self.temp_annotations[idx]
                self.display_image_on_canvas()  # Fixed method call
                self.update_annotations_list()
    
    def update_annotations(self):
        """Update annotations"""
        if not self.image_files:
            return
        
        current_image_name = self.image_files[self.current_image_index]
        visible_annotations = [ann for ann in self.temp_annotations if ann.get('visible', True)]
        
        if visible_annotations:
            self.annotations[current_image_name] = visible_annotations
        elif current_image_name in self.annotations:
            del self.annotations[current_image_name]
        
        self.save_annotations()
        self.update_status("✅ Annotations updated successfully")
    
    def save_annotations(self):
        """Save annotations to file"""
        if not self.images_folder:
            return
        
        annotations_file = os.path.join(self.images_folder, "annotations.txt")
        try:
            with open(annotations_file, 'w') as f:
                for image_name, anns in self.annotations.items():
                    img_width, img_height = self.get_image_dimensions(image_name)
                    
                    for ann in anns:
                        x1, y1, x2, y2 = ann['bbox']
                        center_x = (x1 + x2) / 2 / img_width
                        center_y = (y1 + y2) / 2 / img_height
                        width = (x2 - x1) / img_width
                        height = (y2 - y1) / img_height
                        f.write(f"{image_name},{ann['class']},{center_x:.6f},{center_y:.6f},{width:.6f},{height:.6f}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {e}")
    
    def get_image_dimensions(self, image_name):
        """Get image dimensions"""
        try:
            image_path = os.path.join(self.images_folder, image_name)
            with Image.open(image_path) as img:
                return img.size
        except:
            return 640, 480
    
    def load_existing_annotations(self):
        """Load existing annotations"""
        if not self.images_folder:
            return
        
        annotations_file = os.path.join(self.images_folder, "annotations.txt")
        if os.path.exists(annotations_file):
            try:
                self.annotations = {}
                with open(annotations_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split(',')
                        if len(parts) >= 6:
                            image_name = parts[0]
                            class_name = parts[1]
                            center_x = float(parts[2])
                            center_y = float(parts[3])
                            width = float(parts[4])
                            height = float(parts[5])
                            
                            img_width, img_height = self.get_image_dimensions(image_name)
                            
                            x1 = int((center_x - width/2) * img_width)
                            y1 = int((center_y - height/2) * img_height)
                            x2 = int((center_x + width/2) * img_width)
                            y2 = int((center_y + height/2) * img_height)
                            
                            annotation = {
                                'class': class_name,
                                'bbox': [x1, y1, x2, y2],
                                'visible': True,
                                'color': self.annotation_colors[len(self.annotations.get(image_name, [])) % len(self.annotation_colors)]
                            }
                            
                            if image_name not in self.annotations:
                                self.annotations[image_name] = []
                            self.annotations[image_name].append(annotation)
            except Exception as e:
                print(f"Error loading annotations: {e}")
    
    def preview_annotations(self):
        """Preview annotations"""
        if not self.temp_annotations:
            messagebox.showinfo("Preview", "No annotations to preview for current image.")
            return
        
        preview_text = f"Annotations for {self.image_files[self.current_image_index]}:\n\n"
        for i, ann in enumerate(self.temp_annotations):
            status = "Visible" if ann.get('visible', True) else "Hidden"
            preview_text += f"{i+1}. Class: {ann['class']}\n"
            preview_text += f"   Bbox: {ann['bbox']}\n"
            preview_text += f"   Status: {status}\n"
            preview_text += f"   Color: {ann['color']}\n\n"
        
        messagebox.showinfo("Annotation Preview", preview_text)
    
    def previous_image(self):
        """Go to previous image"""
        if self.image_files and self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()
    
    def next_image(self):
        """Go to next image"""
        if self.image_files and self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()
    
    def train_model(self):
        """Train model placeholder"""
        messagebox.showinfo("Train Model", "🚀 Model training functionality will be implemented in the next phase.\n\nThis will include:\n• Data preprocessing\n• Model architecture selection\n• Training progress monitoring\n• Model evaluation metrics")
    
    def try_model(self):
        """Try model placeholder"""
        messagebox.showinfo("Try Model", "🧪 Model testing functionality will be implemented in the next phase.\n\nThis will include:\n• Load trained models\n• Real-time inference\n• Batch processing\n• Results visualization")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.configure(text=message)
    
    def cleanup_memory(self):
        """Clean up memory"""
        if hasattr(self, 'current_image') and self.current_image:
            self.current_image.close()
        if hasattr(self, 'photo_image') and self.photo_image:
            del self.photo_image
        # Clear thumbnail cache
        self.thumbnail_cache.clear()
    
    def run(self):
        """Start the application main loop"""
        self.root.mainloop()

class ModelManager:
    """Model management placeholder"""
    def __init__(self):
        self.model = None
        self.model_path = ""
    
    def load_model(self, model_path):
        """Load trained model"""
        pass
    
    def predict(self, image_path, prompt=""):
        """Make predictions"""
        pass
    
    def train(self, annotations_data, hyperparams):
        """Train model"""
        pass

class AnalyticsManager:
    """Analytics management placeholder"""
    def __init__(self):
        self.metrics = {}
    
    def calculate_accuracy(self, predicted, ground_truth):
        """Calculate accuracy"""
        pass
    
    def generate_report(self):
        """Generate report"""
        pass

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Configure root window
    root.tk.call('tk', 'scaling', 1.2)  # Improve DPI scaling
    
    # Initialize application
    app = AnnotationTool(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?\n\nAny unsaved annotations will be lost."):
            app.cleanup_memory()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Keyboard shortcuts
    root.bind('<Control-s>', lambda e: app.update_annotations())
    root.bind('<Control-n>', lambda e: app.next_image())
    root.bind('<Control-p>', lambda e: app.previous_image())
    root.bind('<Control-plus>', lambda e: app.zoom_in())
    root.bind('<Control-minus>', lambda e: app.zoom_out())
    root.bind('<Control-0>', lambda e: app.reset_zoom())
    root.bind('<space>', lambda e: app.toggle_boxes_visibility())
    root.bind('<Left>', lambda e: app.previous_image())
    root.bind('<Right>', lambda e: app.next_image())
    
    # Start application
    app.run()

def run():
    """Alternative entry point"""
    main()

if __name__ == "__main__":
    main()