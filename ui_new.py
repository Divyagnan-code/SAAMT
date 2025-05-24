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
import copy

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
    MODEL_ANNOTATION = '#ff9500'
    HANDLE_COLOR = '#00ff00'

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

class UndoRedoManager:
    """Manages undo/redo operations"""
    def __init__(self, max_history=50):
        self.history = []
        self.current_index = -1
        self.max_history = max_history
    
    def save_state(self, state):
        """Save current state"""
        # Remove any future history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(copy.deepcopy(state))
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def undo(self):
        """Undo last operation"""
        if self.current_index > 0:
            self.current_index -= 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def redo(self):
        """Redo next operation"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def can_undo(self):
        return self.current_index > 0
    
    def can_redo(self):
        return self.current_index < len(self.history) - 1

class ModelManager:
    """Manages AI models for annotation"""
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.models_dir = os.path.join(script_dir, "models")
        self.current_model = None
        self.confidence_threshold = 0.5
    
    def get_available_models(self, mode):
        """Get available models for the specified mode"""
        mode_dir = os.path.join(self.models_dir, mode)
        if not os.path.exists(mode_dir):
            os.makedirs(mode_dir, exist_ok=True)
            return []
        
        models = []
        for file in os.listdir(mode_dir):
            if file.endswith(('.pt', '.pth', '.onnx', '.pkl')):
                models.append(file)
        return models
    
    def load_model(self, model_name, mode):
        """Load specified model"""
        model_path = os.path.join(self.models_dir, mode, model_name)
        if os.path.exists(model_path):
            self.current_model = model_name
            print(f"Model {model_name} loaded (placeholder)")
            return True
        return False
    
    def predict(self, image_path, class_filter=None):
        """Make predictions on image (placeholder implementation)"""
        if not self.current_model:
            return []
        
        # Placeholder implementation - returns dummy annotations
        # In real implementation, this would call your AI model
        dummy_annotations = [
            {
                'class': 'person',
                'bbox': [100, 50, 200, 300],
                'confidence': 0.85,
                'color': ModernColors.MODEL_ANNOTATION,
                'is_model_annotation': True
            },
            {
                'class': 'car',
                'bbox': [300, 200, 450, 320],
                'confidence': 0.72,
                'color': ModernColors.MODEL_ANNOTATION,
                'is_model_annotation': True
            }
        ]
        
        # Filter by confidence threshold
        filtered_annotations = [
            ann for ann in dummy_annotations 
            if ann['confidence'] >= self.confidence_threshold
        ]
        
        return filtered_annotations

class AnnotationTool:
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
        self.undo_manager = UndoRedoManager()
        
        # Data structures
        self.images_folder = ""
        self.image_files = []
        self.annotated_images = set()  # Set to keep track of images with completed annotations
        self.current_image_index = 0
        self.current_image = None
        self.photo_image = None
        
        # Annotation data
        self.annotations = {}
        self.temp_annotations = []
        self.last_copied_annotation = None
        self.current_class = "person"
        self.annotation_colors = ['#ff4444', '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff']
        self.color_index = 0
        
        # Drawing and editing state
        self.drawing = False
        self.editing = False
        self.selected_annotation = None
        self.selected_handle = None
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
        
        # Model annotation state
        self.model_annotations = []
        self.reviewing_model_annotations = False
        self.batch_processing = False
        
        # Async loading state
        self.thumbnail_cache = {}
        self.thumbnail_queue = queue.Queue()
        self.loading_thumbnails = False
        self.thumbnail_batch_size = 10
        self.current_batch_start = 0
        
        # Layout state
        self.paned_windows = {}
        
        self.setup_ui()
        self.save_initial_state()
    
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
        style.configure('Modern.Vertical.TProgressbar', background=ModernColors.ACCENT)
    
    def setup_ui(self):
        """Setup the main UI components with resizable layout"""
        # Main container
        main_frame = tk.Frame(self.root, bg=ModernColors.DARK_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create main paned window (vertical split)
        main_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        self.paned_windows['main'] = main_paned
        
        # Top section (toolbar)
        toolbar_frame = tk.Frame(main_paned, bg=ModernColors.SIDEBAR_BG, height=120)
        main_paned.add(toolbar_frame, weight=0)
        self.create_enhanced_toolbar(toolbar_frame)
        
        # Content section
        content_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(content_paned, weight=1)
        self.paned_windows['content'] = content_paned
        
        # Left sidebar
        left_frame = tk.Frame(content_paned, bg=ModernColors.SIDEBAR_BG, width=250)
        content_paned.add(left_frame, weight=0)
        self.create_enhanced_sidebar(left_frame)
        
        # Center canvas area
        center_frame = tk.Frame(content_paned, bg=ModernColors.DARK_BG)
        content_paned.add(center_frame, weight=2)
        self.create_enhanced_canvas_area(center_frame)
        
        # Right controls
        right_frame = tk.Frame(content_paned, bg=ModernColors.SIDEBAR_BG, width=300)
        content_paned.add(right_frame, weight=0)
        self.create_enhanced_right_controls(right_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_enhanced_toolbar(self, parent):
        """Create enhanced toolbar with model controls"""
        toolbar = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG)
        toolbar.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # First row - File and Mode controls
        top_row = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        top_row.pack(fill=tk.X, pady=(0, 5))
        
        # Folder selection
        folder_btn = ModernButton(top_row, text="📁 Select Images Folder", 
                                 command=self.select_folder, font=('Segoe UI', 10, 'bold'),
                                 padx=20, pady=8)
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Mode selection
        mode_frame = tk.Frame(top_row, bg=ModernColors.SIDEBAR_BG)
        mode_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(mode_frame, text="Mode:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                font=('Segoe UI', 9)).pack(anchor=tk.W)
        self.annotation_mode = tk.StringVar(value="bounding_box")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.annotation_mode,
                                 values=["bounding_box", "instance_segmentation", "classification"],
                                 state="readonly", width=18, style='Modern.TCombobox')
        mode_combo.pack()
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # Action buttons
        action_frame = tk.Frame(top_row, bg=ModernColors.SIDEBAR_BG)
        action_frame.pack(side=tk.RIGHT)
        
        try_btn = ModernButton(action_frame, text="🧪 Try Model", 
                              command=self.try_model, bg=ModernColors.BUTTON_WARNING,
                              hover_color='#e86900', font=('Segoe UI', 10), padx=15, pady=8)
        try_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        train_btn = ModernButton(action_frame, text="🚀 Train Model", 
                                command=self.train_model, bg=ModernColors.BUTTON_DANGER,
                                hover_color='#e74856', font=('Segoe UI', 10), padx=15, pady=8)
        train_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Second row - Model controls
        model_row = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        model_row.pack(fill=tk.X, pady=5)
        
        # Model selection
        model_frame = tk.Frame(model_row, bg=ModernColors.SIDEBAR_BG)
        model_frame.pack(side=tk.LEFT)
        
        tk.Label(model_frame, text="AI Model:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                font=('Segoe UI', 9)).pack(anchor=tk.W)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var,
                                       state="readonly", width=25, style='Modern.TCombobox')
        self.model_combo.pack()
        self.model_combo.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # Confidence threshold
        confidence_frame = tk.Frame(model_row, bg=ModernColors.SIDEBAR_BG)
        confidence_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        tk.Label(confidence_frame, text="Confidence:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                font=('Segoe UI', 9)).pack(anchor=tk.W)
        
        conf_control_frame = tk.Frame(confidence_frame, bg=ModernColors.SIDEBAR_BG)
        conf_control_frame.pack()
        
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.confidence_scale = tk.Scale(conf_control_frame, from_=0.1, to=1.0, resolution=0.05,
                                        orient=tk.HORIZONTAL, variable=self.confidence_var,
                                        bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                        highlightthickness=0, length=150)
        self.confidence_scale.pack(side=tk.LEFT)
        
        self.confidence_label = tk.Label(conf_control_frame, text="0.50", 
                                        bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                        font=('Segoe UI', 9), width=5)
        self.confidence_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.confidence_scale.configure(command=self.on_confidence_change)
        
        # Model action buttons
        model_actions = tk.Frame(model_row, bg=ModernColors.SIDEBAR_BG)
        model_actions.pack(side=tk.RIGHT)
        
        ModernButton(model_actions, text="🤖 Annotate Current", 
                    command=self.annotate_current_image, bg='#6f42c1',
                    hover_color='#8a63d2', font=('Segoe UI', 9), padx=12, pady=6).pack(side=tk.LEFT, padx=2)
        
        ModernButton(model_actions, text="📊 Batch Annotate", 
                    command=self.show_batch_dialog, bg='#17a2b8',
                    hover_color='#138496', font=('Segoe UI', 9), padx=12, pady=6).pack(side=tk.LEFT, padx=2)
        
        # Progress section
        self.progress_frame = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
        
        self.progress_label = tk.Label(self.progress_frame, text="", bg=ModernColors.SIDEBAR_BG, 
                                      fg=ModernColors.TEXT_SECONDARY, font=('Segoe UI', 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate',
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack()
        
        # Initialize model list
        self.update_model_list()
    
    def create_enhanced_sidebar(self, parent):
        """Create enhanced left sidebar with scrollable thumbnails"""
        # Header
        header_frame = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(header_frame, text="📷 Images", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Load more button
        self.load_more_btn = ModernButton(header_frame, text="⬇️", 
                                         command=self.load_more_thumbnails, 
                                         bg=ModernColors.BUTTON_SECONDARY,
                                         font=('Segoe UI', 8), padx=8, pady=4)
        self.load_more_btn.pack(side=tk.RIGHT)
        self.load_more_btn.pack_forget()
        
        # Thumbnails container with proper scrolling
        thumb_container = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG)
        thumb_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Create scrollable frame with both vertical and horizontal scrolling
        self.thumb_canvas = tk.Canvas(thumb_container, bg=ModernColors.SIDEBAR_BG, 
                                     highlightthickness=0, bd=0)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(thumb_container, orient="vertical", 
                                   command=self.thumb_canvas.yview)
        h_scrollbar = ttk.Scrollbar(thumb_container, orient="horizontal",
                                   command=self.thumb_canvas.xview)
        
        self.thumb_scrollable_frame = tk.Frame(self.thumb_canvas, bg=ModernColors.SIDEBAR_BG)
        
        # Configure scrolling
        self.thumb_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        )
        
        self.thumb_canvas_window = self.thumb_canvas.create_window((0, 0), 
                                                                  window=self.thumb_scrollable_frame, 
                                                                  anchor="nw")
        self.thumb_canvas.configure(yscrollcommand=v_scrollbar.set, 
                                   xscrollcommand=h_scrollbar.set)
        
        # Enhanced mousewheel scrolling
        def _on_mousewheel(event):
            # Check if shift is held for horizontal scrolling
            if event.state & 0x1:  # Shift key
                self.thumb_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            else:
                self.thumb_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.thumb_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.thumb_scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Update scroll region when canvas size changes
        def _configure_scroll_region(event):
            self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
            canvas_width = event.width
            self.thumb_canvas.itemconfig(self.thumb_canvas_window, width=canvas_width)
        
        self.thumb_canvas.bind('<Configure>', _configure_scroll_region)
        
        # Pack scrollbars and canvas
        self.thumb_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        thumb_container.grid_rowconfigure(0, weight=1)
        thumb_container.grid_columnconfigure(0, weight=1)
    
    def create_enhanced_canvas_area(self, parent):
        """Create enhanced canvas area with editing capabilities"""
        # Canvas controls
        controls_frame = tk.Frame(parent, bg=ModernColors.DARKER_BG, height=60)
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
        
        # Edit controls
        edit_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        edit_frame.pack(side=tk.LEFT, pady=12, padx=20)
        
        ModernButton(edit_frame, text="📋 Copy", command=self.copy_annotation,
                    bg='#28a745', hover_color='#34ce57', font=('Segoe UI', 9), padx=8, pady=4).pack(side=tk.LEFT, padx=2)
        ModernButton(edit_frame, text="📄 Paste", command=self.paste_annotation,
                    bg='#ffc107', hover_color='#ffcd39', font=('Segoe UI', 9), padx=8, pady=4).pack(side=tk.LEFT, padx=2)
        
        # Visibility toggle
        toggle_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
        toggle_frame.pack(side=tk.RIGHT, pady=12, padx=15)
        
        self.visibility_btn = ModernButton(toggle_frame, text="👁️ Hide Boxes", 
                                          command=self.toggle_boxes_visibility,
                                          bg='#6f42c1', hover_color='#8a63d2',
                                          font=('Segoe UI', 9), padx=12, pady=6)
        self.visibility_btn.pack()
        
        # Canvas container
        canvas_container = tk.Frame(parent, bg=ModernColors.BORDER, bd=1, relief=tk.SOLID)
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
        
        # Enhanced canvas events for editing
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
    
    def create_enhanced_right_controls(self, parent):
        """Create enhanced right sidebar with model annotation controls"""
        # Class input section
        class_frame = tk.LabelFrame(parent, text=" 🏷️ Annotation Class ", 
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
        
        # Model annotation review section
        self.review_frame = tk.LabelFrame(parent, text=" 🤖 Model Annotation Review ", 
                                         bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                         font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
        self.review_frame.pack(fill=tk.X, padx=15, pady=10)
        self.review_frame.pack_forget()  # Hidden by default
        
        review_buttons = tk.Frame(self.review_frame, bg=ModernColors.SIDEBAR_BG)
        review_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        ModernButton(review_buttons, text="✅ Approve All", command=self.approve_model_annotations,
                    bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                    font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
        
        ModernButton(review_buttons, text="✏️ Edit & Approve", command=self.edit_model_annotations,
                    bg=ModernColors.BUTTON_WARNING, hover_color='#e86900',
                    font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
        
        ModernButton(review_buttons, text="❌ Reject All", command=self.reject_model_annotations,
                    bg=ModernColors.BUTTON_DANGER, hover_color='#e74856',
                    font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
        
        # Current annotations
        annotations_frame = tk.LabelFrame(parent, text=" 📝 Current Annotations ", 
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
        
        # Bind selection event
        self.annotations_listbox.bind('<<ListboxSelect>>', self.on_annotation_select)
        
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
        action_frame = tk.LabelFrame(parent, text=" ⚡ Actions ", 
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
    
    def save_initial_state(self):
        """Save initial state for undo/redo"""
        self.undo_manager.save_state({
            'temp_annotations': [],
            'current_image_index': 0
        })
    
    def save_state_for_undo(self):
        """Save current state for undo/redo"""
        state = {
            'temp_annotations': copy.deepcopy(self.temp_annotations),
            'current_image_index': self.current_image_index
        }
        self.undo_manager.save_state(state)
    
    def undo_action(self):
        """Undo last action"""
        state = self.undo_manager.undo()
        if state:
            self.temp_annotations = state['temp_annotations']
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("↶ Undo completed")
    
    def redo_action(self):
        """Redo last undone action"""
        state = self.undo_manager.redo()
        if state:
            self.temp_annotations = state['temp_annotations']
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("↷ Redo completed")
    
    def on_mode_change(self, event=None):
        """Handle mode change"""
        self.update_model_list()
    
    def on_model_change(self, event=None):
        """Handle model selection change"""
        model_name = self.model_var.get()
        if model_name:
            mode = self.annotation_mode.get()
            if self.model_manager.load_model(model_name, mode):
                self.update_status(f"Model '{model_name}' loaded successfully")
            else:
                self.update_status(f"Failed to load model '{model_name}'")
    
    def on_confidence_change(self, value):
        """Handle confidence threshold change"""
        self.model_manager.confidence_threshold = float(value)
        self.confidence_label.configure(text=f"{float(value):.2f}")
    
    def update_model_list(self):
        """Update the model dropdown list"""
        mode = self.annotation_mode.get()
        models = self.model_manager.get_available_models(mode)
        self.model_combo['values'] = models
        if models:
            self.model_combo.set(models[0] if models else "")
        else:
            self.model_combo.set("")
    
    def annotate_current_image(self):
        """Annotate current image with AI model"""
        if not self.current_image or not self.model_manager.current_model:
            messagebox.showwarning("Warning", "Please select an image and model first")
            return
        
        current_image_name = self.image_files[self.current_image_index]
        image_path = os.path.join(self.images_folder, current_image_name)
        
        try:
            # Get model predictions
            predictions = self.model_manager.predict(image_path, self.current_class)
            
            if predictions:
                self.model_annotations = predictions
                self.reviewing_model_annotations = True
                self.review_frame.pack(fill=tk.X, padx=15, pady=10, before=self.annotations_listbox.master.master)
                
                # Display model annotations
                self.display_image_on_canvas()
                self.update_status(f"AI found {len(predictions)} annotations. Please review.")
            else:
                messagebox.showinfo("No Annotations", "AI model found no annotations above the confidence threshold.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get model predictions: {e}")
    
    def show_batch_dialog(self):
        """Show batch annotation dialog"""
        if not self.image_files or not self.model_manager.current_model:
            messagebox.showwarning("Warning", "Please select images folder and model first")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch Annotation")
        dialog.geometry("400x300")
        dialog.configure(bg=ModernColors.DARK_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Dialog content
        main_frame = tk.Frame(dialog, bg=ModernColors.DARK_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Batch Annotation Settings", 
                bg=ModernColors.DARK_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Range selection
        range_frame = tk.Frame(main_frame, bg=ModernColors.DARK_BG)
        range_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(range_frame, text="Image Range:", bg=ModernColors.DARK_BG, 
                fg=ModernColors.TEXT_PRIMARY, font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        range_inputs = tk.Frame(range_frame, bg=ModernColors.DARK_BG)
        range_inputs.pack(fill=tk.X, pady=5)
        
        tk.Label(range_inputs, text="From:", bg=ModernColors.DARK_BG, 
                fg=ModernColors.TEXT_SECONDARY, font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        from_var = tk.StringVar(value="1")
        from_entry = tk.Entry(range_inputs, textvariable=from_var, width=8, 
                             font=('Segoe UI', 9), bg=ModernColors.CANVAS_BG, fg='#000000')
        from_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(range_inputs, text="To:", bg=ModernColors.DARK_BG, 
                fg=ModernColors.TEXT_SECONDARY, font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        to_var = tk.StringVar(value=str(len(self.image_files)))
        to_entry = tk.Entry(range_inputs, textvariable=to_var, width=8, 
                           font=('Segoe UI', 9), bg=ModernColors.CANVAS_BG, fg='#000000')
        to_entry.pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = tk.Frame(main_frame, bg=ModernColors.DARK_BG)
        options_frame.pack(fill=tk.X, pady=20)
        
        auto_approve_var = tk.BooleanVar()
        auto_approve_cb = tk.Checkbutton(options_frame, text="Auto-approve high confidence (>0.9)",
                                        variable=auto_approve_var, bg=ModernColors.DARK_BG,
                                        fg=ModernColors.TEXT_PRIMARY, selectcolor=ModernColors.SIDEBAR_BG,
                                        font=('Segoe UI', 9))
        auto_approve_cb.pack(anchor=tk.W, pady=2)
        
        skip_existing_var = tk.BooleanVar(value=True)
        skip_existing_cb = tk.Checkbutton(options_frame, text="Skip images with existing annotations",
                                         variable=skip_existing_var, bg=ModernColors.DARK_BG,
                                         fg=ModernColors.TEXT_PRIMARY, selectcolor=ModernColors.SIDEBAR_BG,
                                         font=('Segoe UI', 9))
        skip_existing_cb.pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=ModernColors.DARK_BG)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def start_batch():
            try:
                from_idx = int(from_var.get()) - 1
                to_idx = int(to_var.get()) - 1
                
                if from_idx < 0 or to_idx >= len(self.image_files) or from_idx > to_idx:
                    messagebox.showerror("Invalid Range", "Please enter a valid image range")
                    return
                
                dialog.destroy()
                self.start_batch_annotation(from_idx, to_idx, auto_approve_var.get(), skip_existing_var.get())
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")
        
        ModernButton(button_frame, text="Start Batch Annotation", command=start_batch,
                    bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                    font=('Segoe UI', 10, 'bold'), pady=8).pack(side=tk.RIGHT, padx=(10, 0))
        
        ModernButton(button_frame, text="Cancel", command=dialog.destroy,
                    bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 10), pady=8).pack(side=tk.RIGHT)
    
    def start_batch_annotation(self, from_idx, to_idx, auto_approve, skip_existing):
        """Start batch annotation process"""
        self.batch_processing = True
        self.progress_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        total_images = to_idx - from_idx + 1
        self.progress_bar.configure(maximum=total_images, value=0)
        self.progress_label.configure(text=f"Processing batch annotation... (0/{total_images})")
        
        def batch_worker():
            processed = 0
            approved = 0
            
            for i in range(from_idx, to_idx + 1):
                if not self.batch_processing:  # Check for cancellation
                    break
                
                image_name = self.image_files[i]
                
                # Skip if has existing annotations and skip_existing is True
                if skip_existing and image_name in self.annotations:
                    processed += 1
                    continue
                
                # Get predictions
                image_path = os.path.join(self.images_folder, image_name)
                try:
                    predictions = self.model_manager.predict(image_path, self.current_class)
                    
                    if predictions:
                        if auto_approve:
                            # Auto-approve high confidence annotations
                            high_conf_annotations = [ann for ann in predictions if ann.get('confidence', 0) > 0.9]
                            if high_conf_annotations:
                                # Convert model annotations to regular annotations
                                for ann in high_conf_annotations:
                                    ann.pop('is_model_annotation', None)
                                    ann.pop('confidence', None)
                                    if 'color' not in ann:
                                        ann['color'] = self.annotation_colors[approved % len(self.annotation_colors)]
                                
                                self.annotations[image_name] = high_conf_annotations
                                approved += len(high_conf_annotations)
                        else:
                            # Save for manual review
                            self.annotations[image_name + "_model_pending"] = predictions
                
                except Exception as e:
                    print(f"Error processing {image_name}: {e}")
                
                processed += 1
                
                # Update progress on main thread
                self.root.after(0, lambda p=processed, t=total_images: self.update_batch_progress(p, t))
            
            # Finish batch processing
            self.root.after(0, lambda: self.finish_batch_annotation(processed, approved))
        
        threading.Thread(target=batch_worker, daemon=True).start()
    
    def update_batch_progress(self, processed, total):
        """Update batch processing progress"""
        self.progress_bar.configure(value=processed)
        self.progress_label.configure(text=f"Processing batch annotation... ({processed}/{total})")
    
    def finish_batch_annotation(self, processed, approved):
        """Finish batch annotation"""
        self.batch_processing = False
        self.progress_frame.pack_forget()
        self.save_annotations()
        
        message = f"Batch annotation completed!\n\nProcessed: {processed} images"
        if approved > 0:
            message += f"\nAuto-approved: {approved} annotations"
        
        messagebox.showinfo("Batch Complete", message)
        self.update_status("Batch annotation completed")
    
    def approve_model_annotations(self):
        """Approve all model annotations"""
        if self.model_annotations:
            self.save_state_for_undo()
            
            # Convert model annotations to regular annotations
            for ann in self.model_annotations:
                ann.pop('is_model_annotation', None)
                ann.pop('confidence', None)
                if 'color' not in ann:
                    ann['color'] = self.annotation_colors[len(self.temp_annotations) % len(self.annotation_colors)]
                self.temp_annotations.append(ann)
            
            self.model_annotations = []
            self.reviewing_model_annotations = False
            self.review_frame.pack_forget()
            
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("✅ Model annotations approved")
    
    def edit_model_annotations(self):
        """Switch to edit mode for model annotations"""
        if self.model_annotations:
            self.approve_model_annotations()  # First approve them
            self.update_status("✏️ Edit mode enabled - Click annotations to modify")
    
    def reject_model_annotations(self):
        """Reject all model annotations"""
        self.model_annotations = []
        self.reviewing_model_annotations = False
        self.review_frame.pack_forget()
        
        self.display_image_on_canvas()
        self.update_status("❌ Model annotations rejected")
    
    def copy_annotation(self):
        """Copy selected annotation"""
        selection = self.annotations_listbox.curselection()
        if selection and selection[0] < len(self.temp_annotations):
            self.last_copied_annotation = copy.deepcopy(self.temp_annotations[selection[0]])
            self.update_status("📋 Annotation copied")
        else:
            messagebox.showwarning("No Selection", "Please select an annotation to copy")
    
    def paste_annotation(self):
        """Paste last copied annotation"""
        if self.last_copied_annotation and self.current_image:
            self.save_state_for_undo()
            
            # Create new annotation with slight offset
            new_annotation = copy.deepcopy(self.last_copied_annotation)
            new_annotation['bbox'][0] += 20  # Offset x
            new_annotation['bbox'][1] += 20  # Offset y
            new_annotation['bbox'][2] += 20  # Offset x
            new_annotation['bbox'][3] += 20  # Offset y
            
            # Ensure it's within image bounds
            if self.current_image:
                img_width, img_height = self.current_image.size
                new_annotation['bbox'][0] = max(0, min(new_annotation['bbox'][0], img_width - 50))
                new_annotation['bbox'][1] = max(0, min(new_annotation['bbox'][1], img_height - 50))
                new_annotation['bbox'][2] = max(new_annotation['bbox'][0] + 50, min(new_annotation['bbox'][2], img_width))
                new_annotation['bbox'][3] = max(new_annotation['bbox'][1] + 50, min(new_annotation['bbox'][3], img_height))
            
            self.temp_annotations.append(new_annotation)
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("📄 Annotation pasted")
        else:
            messagebox.showwarning("Nothing to Paste", "No annotation copied yet")
    
    def on_annotation_select(self, event=None):
        """Handle annotation selection from listbox"""
        selection = self.annotations_listbox.curselection()
        if selection and selection[0] < len(self.temp_annotations):
            self.selected_annotation = selection[0]
            self.display_image_on_canvas()  # Refresh display to show selection
    
    def get_annotation_at_point(self, x, y):
        """Get annotation index at given canvas coordinates"""
        # Convert canvas coordinates to image coordinates
        img_x = (x - self.pan_x) / self.zoom_factor
        img_y = (y - self.pan_y) / self.zoom_factor
        
        # Check all annotations (reverse order to get topmost)
        for i in reversed(range(len(self.temp_annotations))):
            ann = self.temp_annotations[i]
            bbox = ann['bbox']
            if (bbox[0] <= img_x <= bbox[2] and bbox[1] <= img_y <= bbox[3]):
                return i
        
        # Check model annotations
        for i in reversed(range(len(self.model_annotations))):
            ann = self.model_annotations[i]
            bbox = ann['bbox']
            if (bbox[0] <= img_x <= bbox[2] and bbox[1] <= img_y <= bbox[3]):
                return f"model_{i}"
        
        return None
    
    def get_resize_handle_at_point(self, x, y, annotation_idx):
        """Get resize handle at given point for annotation"""
        if annotation_idx is None or isinstance(annotation_idx, str):
            return None
        
        if annotation_idx >= len(self.temp_annotations):
            return None
        
        bbox = self.temp_annotations[annotation_idx]['bbox']
        
        # Convert to canvas coordinates
        x1 = bbox[0] * self.zoom_factor + self.pan_x
        y1 = bbox[1] * self.zoom_factor + self.pan_y
        x2 = bbox[2] * self.zoom_factor + self.pan_x
        y2 = bbox[3] * self.zoom_factor + self.pan_y
        
        handle_size = 8
        handles = {
            'nw': (x1, y1),
            'ne': (x2, y1),
            'sw': (x1, y2),
            'se': (x2, y2),
            'n': ((x1 + x2) / 2, y1),
            's': ((x1 + x2) / 2, y2),
            'w': (x1, (y1 + y2) / 2),
            'e': (x2, (y1 + y2) / 2)
        }
        
        for handle_name, (hx, hy) in handles.items():
            if abs(x - hx) <= handle_size and abs(y - hy) <= handle_size:
                return handle_name
        
        return None
    
    def on_canvas_click(self, event):
        """Enhanced canvas click handling"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check if clicking on annotation
        clicked_annotation = self.get_annotation_at_point(canvas_x, canvas_y)
        
        if clicked_annotation is not None:
            if isinstance(clicked_annotation, str) and clicked_annotation.startswith("model_"):
                # Clicked on model annotation - just select it
                self.update_status("Click approve/reject buttons to handle model annotations")
                return
            
            # Check for resize handle
            handle = self.get_resize_handle_at_point(canvas_x, canvas_y, clicked_annotation)
            
            if handle:
                # Start resizing
                self.editing = True
                self.selected_annotation = clicked_annotation
                self.selected_handle = handle
                self.start_x = canvas_x
                self.start_y = canvas_y
                self.canvas.configure(cursor="sizing")
            else:
                # Start moving
                self.editing = True
                self.selected_annotation = clicked_annotation
                self.selected_handle = "move"
                self.start_x = canvas_x
                self.start_y = canvas_y
                self.canvas.configure(cursor="fleur")
                
                # Select in listbox
                self.annotations_listbox.selection_clear(0, tk.END)
                self.annotations_listbox.selection_set(clicked_annotation)
        else:
            # Start drawing new annotation
            if self.annotation_mode.get() == "bounding_box":
                self.start_drawing(event)
    
    def on_canvas_drag(self, event):
        """Enhanced canvas drag handling"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        if self.editing and self.selected_annotation is not None:
            self.handle_annotation_edit(canvas_x, canvas_y)
        elif self.drawing:
            self.draw_temp_bbox(event)
    
    def handle_annotation_edit(self, canvas_x, canvas_y):
        """Handle annotation editing (move/resize)"""
        if self.selected_annotation >= len(self.temp_annotations):
            return
        
        dx = canvas_x - self.start_x
        dy = canvas_y - self.start_y
        
        # Convert to image coordinates
        img_dx = dx / self.zoom_factor
        img_dy = dy / self.zoom_factor
        
        bbox = self.temp_annotations[self.selected_annotation]['bbox']
        
        if self.selected_handle == "move":
            # Move entire annotation
            bbox[0] += img_dx
            bbox[1] += img_dy
            bbox[2] += img_dx
            bbox[3] += img_dy
        else:
            # Resize annotation
            if 'n' in self.selected_handle:
                bbox[1] += img_dy
            if 's' in self.selected_handle:
                bbox[3] += img_dy
            if 'w' in self.selected_handle:
                bbox[0] += img_dx
            if 'e' in self.selected_handle:
                bbox[2] += img_dx
            
            # Ensure minimum size
            if bbox[2] - bbox[0] < 10:
                if 'w' in self.selected_handle:
                    bbox[0] = bbox[2] - 10
                else:
                    bbox[2] = bbox[0] + 10
            
            if bbox[3] - bbox[1] < 10:
                if 'n' in self.selected_handle:
                    bbox[1] = bbox[3] - 10
                else:
                    bbox[3] = bbox[1] + 10
        
        # Constrain to image bounds
        if self.current_image:
            img_width, img_height = self.current_image.size
            bbox[0] = max(0, min(bbox[0], img_width))
            bbox[1] = max(0, min(bbox[1], img_height))
            bbox[2] = max(0, min(bbox[2], img_width))
            bbox[3] = max(0, min(bbox[3], img_height))
        
        self.start_x = canvas_x
        self.start_y = canvas_y
        
        self.display_image_on_canvas()
        self.update_annotations_list()
    
    def on_canvas_release(self, event):
        """Enhanced canvas release handling"""
        if self.editing:
            if self.selected_annotation is not None:
                self.save_state_for_undo()
            self.editing = False
            self.selected_handle = None
            self.canvas.configure(cursor="crosshair")
        elif self.drawing:
            self.finish_drawing(event)
    
    def on_right_click(self, event):
        """Handle right click"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check if right-clicking on annotation
        clicked_annotation = self.get_annotation_at_point(canvas_x, canvas_y)
        
        if clicked_annotation is not None and not isinstance(clicked_annotation, str):
            # Show context menu for annotation
            self.show_annotation_context_menu(event, clicked_annotation)
        else:
            # Start panning
            self.start_pan(event)
    
    def show_annotation_context_menu(self, event, annotation_idx):
        """Show context menu for annotation"""
        context_menu = tk.Menu(self.root, tearoff=0, bg=ModernColors.SIDEBAR_BG, 
                              fg=ModernColors.TEXT_PRIMARY)
        
        context_menu.add_command(label="🎨 Change Color", 
                                command=lambda: self.change_annotation_color_by_index(annotation_idx))
        context_menu.add_command(label="📋 Copy", 
                                command=lambda: self.copy_annotation_by_index(annotation_idx))
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Delete", 
                                command=lambda: self.delete_annotation_by_index(annotation_idx))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def change_annotation_color_by_index(self, idx):
        """Change annotation color by index"""
        if 0 <= idx < len(self.temp_annotations):
            color = colorchooser.askcolor(title="Choose annotation color")[1]
            if color:
                self.temp_annotations[idx]['color'] = color
                self.display_image_on_canvas()
    
    def copy_annotation_by_index(self, idx):
        """Copy annotation by index"""
        if 0 <= idx < len(self.temp_annotations):
            self.last_copied_annotation = copy.deepcopy(self.temp_annotations[idx])
            self.update_status("📋 Annotation copied")
    
    def delete_annotation_by_index(self, idx):
        """Delete annotation by index"""
        if 0 <= idx < len(self.temp_annotations):
            self.save_state_for_undo()
            del self.temp_annotations[idx]
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("🗑️ Annotation deleted")
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for cursor changes"""
        if self.editing or self.drawing or self.panning:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check if hovering over annotation
        hovered_annotation = self.get_annotation_at_point(canvas_x, canvas_y)
        
        if hovered_annotation is not None and not isinstance(hovered_annotation, str):
            # Check for resize handle
            handle = self.get_resize_handle_at_point(canvas_x, canvas_y, hovered_annotation)
            
            if handle:
                # Set appropriate cursor for resize handle
                cursor_map = {
                    'nw': 'top_left_corner',
                    'ne': 'top_right_corner',
                    'sw': 'bottom_left_corner',
                    'se': 'bottom_right_corner',
                    'n': 'top_side',
                    's': 'bottom_side',
                    'w': 'left_side',
                    'e': 'right_side'
                }
                self.canvas.configure(cursor=cursor_map.get(handle, 'sizing'))
            else:
                self.canvas.configure(cursor="fleur")  # Move cursor
        else:
            self.canvas.configure(cursor="crosshair")  # Default cursor
    
    def on_double_click(self, event):
        """Handle double click to edit annotation class"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        clicked_annotation = self.get_annotation_at_point(canvas_x, canvas_y)
        
        if clicked_annotation is not None and not isinstance(clicked_annotation, str):
            self.edit_annotation_class(clicked_annotation)
    
    def edit_annotation_class(self, annotation_idx):
        """Edit annotation class"""
        if 0 <= annotation_idx < len(self.temp_annotations):
            current_class = self.temp_annotations[annotation_idx]['class']
            
            # Create simple dialog
            new_class = tk.simpledialog.askstring("Edit Class", 
                                                 f"Current class: {current_class}\nEnter new class:",
                                                 initialvalue=current_class)
            
            if new_class and new_class.strip():
                self.save_state_for_undo()
                self.temp_annotations[annotation_idx]['class'] = new_class.strip()
                self.display_image_on_canvas()
                self.update_annotations_list()
                self.update_status(f"✏️ Class changed to '{new_class.strip()}'")
    
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
            
            # Initialize or update annotated images set
            # If annotations exist for an image, consider it potentially annotated
            self.annotated_images = set()
            
            self.load_existing_annotations()
            self.start_thumbnail_loading()
            self.load_current_image()
            
            # Update annotated images tab
            if hasattr(self, 'annotated_thumb_scrollable_frame'):
                self.update_annotated_thumbnails()
            
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
            
            # Image name and status
            info_frame = tk.Frame(thumb_frame, bg=ModernColors.SIDEBAR_BG)
            info_frame.pack(fill=tk.X, padx=5)
            
            name_label = tk.Label(info_frame, 
                                 text=f"{thumb_data['index']+1}. {thumb_data['file'][:18]}{'...' if len(thumb_data['file']) > 18 else ''}",
                                 bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                 font=('Segoe UI', 8), wraplength=180, justify=tk.LEFT)
            name_label.pack(anchor=tk.W)
            
            # Annotation count
            ann_count = 0
            if thumb_data['file'] in self.annotations:
                ann_count = len(self.annotations[thumb_data['file']])
            
            status_text = f"📝 {ann_count} annotations" if ann_count > 0 else "No annotations"
            status_label = tk.Label(info_frame, text=status_text,
                                   bg=ModernColors.SIDEBAR_BG, 
                                   fg=ModernColors.ACCENT if ann_count > 0 else ModernColors.TEXT_SECONDARY,
                                   font=('Segoe UI', 7))
            status_label.pack(anchor=tk.W, pady=(0, 3))
            
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
            status_label.bind('<Enter>', on_enter)
            status_label.bind('<Leave>', on_leave)
        
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
        if not self.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        try:
            image_number = int(self.jump_entry.get())
            if 1 <= image_number <= len(self.image_files):
                self.current_image_index = image_number - 1
                self.load_current_image()
                self.update_status(f"Navigated to image {image_number} of {len(self.image_files)}")
            else:
                messagebox.showwarning("Invalid Number", f"Please enter a number between 1 and {len(self.image_files)}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number.")
    
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
        """Display image on canvas with annotations"""
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
            for i, ann in enumerate(self.annotations[current_image_name]):
                if ann.get('visible', True):
                    self.draw_bbox(ann['bbox'], ann['color'], ann['class'], 
                                 selected=(i == self.selected_annotation))
        
        # Draw temporary annotations
        for i, ann in enumerate(self.temp_annotations):
            if ann.get('visible', True):
                self.draw_bbox(ann['bbox'], ann['color'], ann['class'], 
                             selected=(i == self.selected_annotation))
        
        # Draw model annotations with different style
        for i, ann in enumerate(self.model_annotations):
            if ann.get('visible', True):
                confidence = ann.get('confidence', 0)
                label = f"{ann['class']} ({confidence:.2f})"
                self.draw_bbox(ann['bbox'], ann['color'], label, is_model=True)
    
    def draw_bbox(self, bbox, color, class_name, selected=False, is_model=False):
        """Draw bounding box on canvas with handles if selected"""
        x1, y1, x2, y2 = bbox
        
        # Scale coordinates
        x1 = x1 * self.zoom_factor + self.pan_x
        y1 = y1 * self.zoom_factor + self.pan_y
        x2 = x2 * self.zoom_factor + self.pan_x
        y2 = y2 * self.zoom_factor + self.pan_y
        
        # Draw rectangle
        line_width = 4 if is_model else 3
        line_style = [10, 5] if is_model else []  # Dashed for model annotations
        
        rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=line_width, 
                                              tags="annotation", dash=line_style)
        
        # Draw class label background
        label_bg = self.canvas.create_rectangle(x1-1, y1-25, x1+len(class_name)*8+15, y1, 
                                              fill=color, outline=color, tags="annotation")
        
        # Draw class label text
        self.canvas.create_text(x1+7, y1-12, text=class_name, fill='white', anchor=tk.W, 
                               font=('Segoe UI', 9, 'bold'), tags="annotation")
        
        # Draw resize handles if selected
        if selected and not is_model:
            self.draw_resize_handles(x1, y1, x2, y2)
    
    def draw_resize_handles(self, x1, y1, x2, y2):
        """Draw resize handles for selected annotation"""
        handle_size = 8
        handle_color = ModernColors.HANDLE_COLOR
        
        handles = [
            (x1, y1),  # nw
            (x2, y1),  # ne
            (x1, y2),  # sw
            (x2, y2),  # se
            ((x1 + x2) / 2, y1),  # n
            ((x1 + x2) / 2, y2),  # s
            (x1, (y1 + y2) / 2),  # w
            (x2, (y1 + y2) / 2),  # e
        ]
        
        for hx, hy in handles:
            self.canvas.create_rectangle(hx - handle_size//2, hy - handle_size//2,
                                       hx + handle_size//2, hy + handle_size//2,
                                       fill=handle_color, outline='black', width=1,
                                       tags="handle")
    
    def start_drawing(self, event):
        """Start drawing bounding box"""
        self.drawing = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
    
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
            self.save_state_for_undo()
            
            annotation = {
                'class': self.current_class,
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'visible': True,
                'color': self.annotation_colors[self.color_index % len(self.annotation_colors)]
            }
            self.temp_annotations.append(annotation)
            self.color_index += 1
            self.display_image_on_canvas()
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
            self.display_image_on_canvas()
    
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
            self.display_image_on_canvas()
    
    def zoom_out(self):
        """Zoom out"""
        if self.zoom_factor > 0.1:
            self.zoom_factor /= 1.2
            self.display_image_on_canvas()
    
    def reset_zoom(self):
        """Reset zoom and pan"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_image_on_canvas()
    
    def toggle_boxes_visibility(self):
        """Toggle bounding box visibility"""
        self.boxes_visible = not self.boxes_visible
        self.display_image_on_canvas()
        status = "visible" if self.boxes_visible else "hidden"
        self.update_status(f"Bounding boxes {status}")
        self.visibility_btn.configure(text="👁️ Show Boxes" if not self.boxes_visible else "👁️ Hide Boxes")
    
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
            model_indicator = " 🤖" if ann.get('is_model_annotation') else ""
            self.annotations_listbox.insert(tk.END, f"{status} {ann['class']}: {bbox_str}{model_indicator}")
    
    def change_annotation_color(self):
        """Change annotation color"""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.temp_annotations):
                color = colorchooser.askcolor(title="Choose annotation color")[1]
                if color:
                    self.temp_annotations[idx]['color'] = color
                    self.display_image_on_canvas()
    
    def delete_selected_annotation(self):
        """Delete selected annotation"""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.temp_annotations):
                self.save_state_for_undo()
                del self.temp_annotations[idx]
                self.display_image_on_canvas()
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
    
    def complete_current_annotation(self):
        """Mark current image as completely annotated"""
        if not self.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        current_image_name = self.image_files[self.current_image_index]
        
        # First make sure annotations are updated
        self.update_annotations()
        
        # Mark as annotated
        if current_image_name in self.annotations and len(self.annotations[current_image_name]) > 0:
            self.annotated_images.add(current_image_name)
            self.update_status(f"✅ Image {current_image_name} marked as completely annotated")
            
            # Update the annotated images tab with this image
            self.update_annotated_thumbnails()
            
            # Move to next image if available
            if self.current_image_index < len(self.image_files) - 1:
                self.current_image_index += 1
                self.load_current_image()
        else:
            messagebox.showwarning("No Annotations", "Please add at least one annotation before completing.")
    
    def update_annotated_thumbnails(self):
        """Update the annotated images thumbnails"""
        # Clear existing thumbnails
        for widget in self.annotated_thumb_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Filter images that are marked as annotated
        annotated_files = [img for img in self.image_files if img in self.annotated_images]
        
        if not annotated_files:
            # Show a message if no annotated images
            msg_label = tk.Label(self.annotated_thumb_scrollable_frame, 
                                text="No completed annotations yet", 
                                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                font=('Segoe UI', 10))
            msg_label.pack(pady=20)
            return
        
        # Load thumbnails for annotated images
        for i, image_file in enumerate(annotated_files):
            try:
                # Check if we already have this thumbnail
                idx = self.image_files.index(image_file)
                if idx in self.thumbnail_cache:
                    photo = self.thumbnail_cache[idx]
                else:
                    # Create a new thumbnail
                    image_path = os.path.join(self.images_folder, image_file)
                    with Image.open(image_path) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Create thumbnail
                        img.thumbnail((160, 120), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.thumbnail_cache[idx] = photo
                
                # Create thumbnail frame
                thumb_frame = tk.Frame(self.annotated_thumb_scrollable_frame, bg=ModernColors.SIDEBAR_BG, 
                                      relief=tk.SOLID, bd=1)
                thumb_frame.pack(fill=tk.X, padx=5, pady=3)
                
                # Thumbnail button
                thumb_btn = tk.Button(thumb_frame, image=photo, 
                                     bg=ModernColors.SIDEBAR_BG, bd=0, relief=tk.FLAT,
                                     cursor='hand2',
                                     command=lambda idx=idx: self.jump_to_image(idx))
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
                ann_count = len(self.annotations[image_file])
                status_text = f"📝 {ann_count} annotations"
                status_label = tk.Label(info_frame, text=status_text,
                                       bg=ModernColors.SIDEBAR_BG, 
                                       fg=ModernColors.ACCENT,
                                       font=('Segoe UI', 7))
                status_label.pack(anchor=tk.W, pady=(0, 3))
                
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
                status_label.bind('<Enter>', on_enter)
                status_label.bind('<Leave>', on_leave)
                
            except Exception as e:
                print(f"Error creating annotated thumbnail for {image_file}: {e}")
    
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
    
    def complete_current_annotation(self):
        """Mark current image as completely annotated"""
        if not self.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        current_image_name = self.image_files[self.current_image_index]
        
        # First make sure annotations are updated
        self.update_annotations()
        
        # Mark as annotated
        if current_image_name in self.annotations and len(self.annotations[current_image_name]) > 0:
            self.annotated_images.add(current_image_name)
            self.update_status(f"✅ Image {current_image_name} marked as completely annotated")
            
            # Update the annotated images tab with this image
            if hasattr(self, 'annotated_thumb_scrollable_frame'):
                self.update_annotated_thumbnails()
            
            # Move to next image if available
            if self.current_image_index < len(self.image_files) - 1:
                self.current_image_index += 1
                self.load_current_image()
        else:
            messagebox.showwarning("No Annotations", "Please add at least one annotation before completing.")
    
    def update_annotated_thumbnails(self):
        """Update the annotated images thumbnails"""
        # Clear existing thumbnails
        for widget in self.annotated_thumb_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Filter images that are marked as annotated
        annotated_files = [img for img in self.image_files if img in self.annotated_images]
        
        if not annotated_files:
            # Show a message if no annotated images
            msg_label = tk.Label(self.annotated_thumb_scrollable_frame, 
                                text="No completed annotations yet", 
                                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                font=('Segoe UI', 10))
            msg_label.pack(pady=20)
            return
        
        # Load thumbnails for annotated images
        for i, image_file in enumerate(annotated_files):
            try:
                # Check if we already have this thumbnail
                idx = self.image_files.index(image_file)
                if idx in self.thumbnail_cache:
                    photo = self.thumbnail_cache[idx]
                else:
                    # Create a new thumbnail
                    image_path = os.path.join(self.images_folder, image_file)
                    with Image.open(image_path) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Create thumbnail
                        img.thumbnail((160, 120), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.thumbnail_cache[idx] = photo
                
                # Create thumbnail frame
                thumb_frame = tk.Frame(self.annotated_thumb_scrollable_frame, bg=ModernColors.SIDEBAR_BG, 
                                      relief=tk.SOLID, bd=1)
                thumb_frame.pack(fill=tk.X, padx=5, pady=3)
                
                # Thumbnail button
                thumb_btn = tk.Button(thumb_frame, image=photo, 
                                     bg=ModernColors.SIDEBAR_BG, bd=0, relief=tk.FLAT,
                                     cursor='hand2',
                                     command=lambda idx=idx: self.jump_to_image(idx))
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
                ann_count = len(self.annotations[image_file])
                status_text = f"📝 {ann_count} annotations"
                status_label = tk.Label(info_frame, text=status_text,
                                       bg=ModernColors.SIDEBAR_BG, 
                                       fg=ModernColors.ACCENT,
                                       font=('Segoe UI', 7))
                status_label.pack(anchor=tk.W, pady=(0, 3))
                
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
                status_label.bind('<Enter>', on_enter)
                status_label.bind('<Leave>', on_leave)
                
            except Exception as e:
                print(f"Error creating annotated thumbnail for {image_file}: {e}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.configure(text=message)
    
    def toggle_boxes_visibility(self):
        """Toggle the visibility of annotation boxes"""
        if not hasattr(self, 'boxes_visible'):
            self.boxes_visible = True
        
        # Toggle state
        self.boxes_visible = not self.boxes_visible
        
        if self.boxes_visible:
            # Show boxes
            self.redraw_annotations()
            self.update_status("👁️ Bounding boxes are now visible")
            if hasattr(self, 'visibility_btn'):
                self.visibility_btn.configure(text="👁️ Hide Boxes")
        else:
            # Hide boxes
            self.canvas.delete('annotation')
            self.canvas.delete('selected')
            self.update_status("👂 Bounding boxes are now hidden")
            if hasattr(self, 'visibility_btn'):
                self.visibility_btn.configure(text="👁️ Show Boxes")
    
    def jump_to_image_by_number(self):
        """Jump to a specific image by its number"""
        if not self.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        try:
            if not hasattr(self, 'jump_entry') or not self.jump_entry:
                return
            
            # Get the number from the entry field
            image_number = int(self.jump_entry.get())
            
            # Check if the number is valid
            if image_number < 1 or image_number > len(self.image_files):
                messagebox.showwarning("Invalid Number", 
                                    f"Please enter a number between 1 and {len(self.image_files)}")
                return
            
            # Adjust for 0-based indexing
            target_index = image_number - 1
            
            # Jump to the image
            self.jump_to_image(target_index)
            self.update_status(f"Navigated to image {image_number} of {len(self.image_files)}")
            
            # Clear the entry field
            self.jump_entry.delete(0, tk.END)
            
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def jump_to_image(self, index):
        """Jump directly to an image by its index"""
        if not self.image_files:
            return
        
        # Make sure index is valid
        if index < 0 or index >= len(self.image_files):
            return
        
        # Save current annotations before jumping
        self.update_annotations()
        
        # Update index and load the image
        self.current_image_index = index
        self.load_current_image()
    
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
    
    # Enhanced keyboard shortcuts
    root.bind('<Control-s>', lambda e: app.update_annotations())
    root.bind('<Control-n>', lambda e: app.next_image())
    root.bind('<Control-p>', lambda e: app.previous_image())
    root.bind('<Control-plus>', lambda e: app.zoom_in())
    root.bind('<Control-minus>', lambda e: app.zoom_out())
    root.bind('<Control-0>', lambda e: app.reset_zoom())
    root.bind('<space>', lambda e: app.toggle_boxes_visibility())
    root.bind('<Left>', lambda e: app.previous_image())
    root.bind('<Right>', lambda e: app.next_image())
    
    # Undo/Redo shortcuts
    root.bind('<Control-z>', lambda e: app.undo_action())
    root.bind('<Control-y>', lambda e: app.redo_action())
    root.bind('<Control-Shift-Z>', lambda e: app.redo_action())
    
    # Copy/Paste shortcuts
    root.bind('<Control-c>', lambda e: app.copy_annotation())
    root.bind('<Control-v>', lambda e: app.paste_annotation())
    
    # Delete shortcut
    root.bind('<Delete>', lambda e: app.delete_selected_annotation())
    root.bind('<BackSpace>', lambda e: app.delete_selected_annotation())
    
    # Focus handling for proper keyboard shortcuts
    def on_focus_in(event):
        if hasattr(event.widget, 'winfo_class'):
            if event.widget.winfo_class() not in ['Entry', 'Text', 'Listbox']:
                root.focus_set()
    
    root.bind_all('<FocusIn>', on_focus_in)
    
    # Start application
    app.run()

def run():
    """Alternative entry point"""
    main()

if __name__ == "__main__":
    main()