import tkinter as tk
from tkinter import ttk
from event_handlers import (
    select_folder_handler, previous_image_handler, next_image_handler,
    zoom_in_handler, zoom_out_handler, reset_zoom_handler,
    try_model_handler, train_model_handler, on_mode_change_handler,
    on_model_change_handler, on_confidence_change_handler,
    jump_to_image_by_number_handler, toggle_boxes_visibility_handler,
    show_annotation_list_context_menu_handler # Import the new handler
)
# ModernColors and ModernButton classes are defined below in this file.

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

# --- Start of new UI creation functions ---

def create_enhanced_toolbar(parent_frame, app):
    """Create enhanced toolbar with model controls"""
    toolbar = tk.Frame(parent_frame, bg=ModernColors.SIDEBAR_BG)
    toolbar.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # First row - File and Mode controls
    top_row = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
    top_row.pack(fill=tk.X, pady=(0, 5))
    
    # Folder selection
    folder_btn = ModernButton(top_row, text="📁 Select Images Folder", 
                             command=lambda: select_folder_handler(app), font=('Segoe UI', 10, 'bold'),
                             padx=20, pady=8)
    folder_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # Mode selection
    mode_frame = tk.Frame(top_row, bg=ModernColors.SIDEBAR_BG)
    mode_frame.pack(side=tk.LEFT, padx=10)
    
    tk.Label(mode_frame, text="Mode:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
            font=('Segoe UI', 9)).pack(anchor=tk.W)
    app.annotation_mode = tk.StringVar(value="bounding_box")
    mode_combo = ttk.Combobox(mode_frame, textvariable=app.annotation_mode,
                             values=["bounding_box", "instance_segmentation", "classification"],
                             state="readonly", width=18, style='Modern.TCombobox')
    mode_combo.pack()
    mode_combo.bind('<<ComboboxSelected>>', lambda event: on_mode_change_handler(app, event))
    
    # Action buttons
    action_frame = tk.Frame(top_row, bg=ModernColors.SIDEBAR_BG)
    action_frame.pack(side=tk.RIGHT)
    
    try_btn = ModernButton(action_frame, text="🧪 Try Model", 
                          command=lambda: try_model_handler(app), bg=ModernColors.BUTTON_WARNING,
                          hover_color='#e86900', font=('Segoe UI', 10), padx=15, pady=8)
    try_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    train_btn = ModernButton(action_frame, text="🚀 Train Model", 
                            command=lambda: train_model_handler(app), bg=ModernColors.BUTTON_DANGER,
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
    app.model_var = tk.StringVar()
    app.model_combo = ttk.Combobox(model_frame, textvariable=app.model_var,
                                   state="readonly", width=25, style='Modern.TCombobox')
    app.model_combo.pack()
    app.model_combo.bind('<<ComboboxSelected>>', lambda event: on_model_change_handler(app, event))
    
    # Confidence threshold
    confidence_frame = tk.Frame(model_row, bg=ModernColors.SIDEBAR_BG)
    confidence_frame.pack(side=tk.LEFT, padx=(20, 0))
    
    tk.Label(confidence_frame, text="Confidence:", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
            font=('Segoe UI', 9)).pack(anchor=tk.W)
    
    conf_control_frame = tk.Frame(confidence_frame, bg=ModernColors.SIDEBAR_BG)
    conf_control_frame.pack()
    
    app.confidence_var = tk.DoubleVar(value=0.5)
    app.confidence_scale = tk.Scale(conf_control_frame, from_=0.1, to=1.0, resolution=0.05,
                                    orient=tk.HORIZONTAL, variable=app.confidence_var,
                                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                    highlightthickness=0, length=150)
    app.confidence_scale.pack(side=tk.LEFT)
    
    app.confidence_label = tk.Label(conf_control_frame, text="0.50", 
                                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                    font=('Segoe UI', 9), width=5)
    app.confidence_label.pack(side=tk.LEFT, padx=(5, 0))
    
    app.confidence_scale.configure(command=lambda value: on_confidence_change_handler(app, value))
    
    # Model action buttons
    model_actions = tk.Frame(model_row, bg=ModernColors.SIDEBAR_BG)
    model_actions.pack(side=tk.RIGHT)
    
    ModernButton(model_actions, text="🤖 Annotate Current", 
                command=app.annotate_current_image, bg='#6f42c1',
                hover_color='#8a63d2', font=('Segoe UI', 9), padx=12, pady=6).pack(side=tk.LEFT, padx=2)
    
    ModernButton(model_actions, text="📊 Batch Annotate", 
                command=app.show_batch_dialog, bg='#17a2b8',
                hover_color='#138496', font=('Segoe UI', 9), padx=12, pady=6).pack(side=tk.LEFT, padx=2)
    
    # Progress section
    app.progress_frame = tk.Frame(toolbar, bg=ModernColors.SIDEBAR_BG)
    
    app.progress_label = tk.Label(app.progress_frame, text="", bg=ModernColors.SIDEBAR_BG, 
                                  fg=ModernColors.TEXT_SECONDARY, font=('Segoe UI', 9))
    app.progress_label.pack()
    
    app.progress_bar = ttk.Progressbar(app.progress_frame, length=400, mode='determinate',
                                       style='Modern.Horizontal.TProgressbar')
    app.progress_bar.pack()
    
    # Initialize model list - this call might need to be in AnnotationTool after UI setup
    app.update_model_list()


def create_enhanced_sidebar(parent_frame, app):
    """Create enhanced left sidebar with scrollable thumbnails"""
    # Header
    header_frame = tk.Frame(parent_frame, bg=ModernColors.SIDEBAR_BG)
    header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    tk.Label(header_frame, text="📷 Images", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
            font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
    
    # Load more button
    app.load_more_btn = ModernButton(header_frame, text="⬇️", 
                                     command=app.load_more_thumbnails, 
                                     bg=ModernColors.BUTTON_SECONDARY,
                                     font=('Segoe UI', 8), padx=8, pady=4)
    app.load_more_btn.pack(side=tk.RIGHT)
    app.load_more_btn.pack_forget()
    
    # Thumbnails container with proper scrolling
    thumb_container = tk.Frame(parent_frame, bg=ModernColors.SIDEBAR_BG)
    thumb_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
    
    # Create scrollable frame with both vertical and horizontal scrolling
    app.thumb_canvas = tk.Canvas(thumb_container, bg=ModernColors.SIDEBAR_BG, 
                                 highlightthickness=0, bd=0)
    
    # Scrollbars
    v_scrollbar = ttk.Scrollbar(thumb_container, orient="vertical", 
                               command=app.thumb_canvas.yview)
    h_scrollbar = ttk.Scrollbar(thumb_container, orient="horizontal",
                               command=app.thumb_canvas.xview)
    
    app.thumb_scrollable_frame = tk.Frame(app.thumb_canvas, bg=ModernColors.SIDEBAR_BG)
    
    # Configure scrolling
    app.thumb_scrollable_frame.bind(
        "<Configure>",
        lambda e: app.thumb_canvas.configure(scrollregion=app.thumb_canvas.bbox("all"))
    )
    
    app.thumb_canvas_window = app.thumb_canvas.create_window((0, 0), 
                                                              window=app.thumb_scrollable_frame, 
                                                              anchor="nw")
    app.thumb_canvas.configure(yscrollcommand=v_scrollbar.set, 
                               xscrollcommand=h_scrollbar.set)
    
    # Enhanced mousewheel scrolling
    def _on_mousewheel(event):
        # Check if shift is held for horizontal scrolling
        if event.state & 0x1:  # Shift key
            app.thumb_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        else:
            app.thumb_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    app.thumb_canvas.bind("<MouseWheel>", _on_mousewheel)
    app.thumb_scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    
    # Update scroll region when canvas size changes
    def _configure_scroll_region(event):
        app.thumb_canvas.configure(scrollregion=app.thumb_canvas.bbox("all"))
        canvas_width = event.width
        app.thumb_canvas.itemconfig(app.thumb_canvas_window, width=canvas_width)
    
    app.thumb_canvas.bind('<Configure>', _configure_scroll_region)
    
    # Pack scrollbars and canvas
    app.thumb_canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    thumb_container.grid_rowconfigure(0, weight=1)
    thumb_container.grid_columnconfigure(0, weight=1)


def create_enhanced_canvas_area(parent_frame, app):
    """Create enhanced canvas area with editing capabilities"""
    # Canvas controls
    controls_frame = tk.Frame(parent_frame, bg=ModernColors.DARKER_BG, height=60)
    controls_frame.pack(fill=tk.X, pady=(0, 5))
    controls_frame.pack_propagate(False)
    
    # Navigation section
    nav_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
    nav_frame.pack(side=tk.LEFT, pady=12, padx=15)
    
    prev_btn = ModernButton(nav_frame, text="◀ Previous", command=lambda: previous_image_handler(app),
                           bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=12, pady=6)
    prev_btn.pack(side=tk.LEFT, padx=(0, 8))
    
    next_btn = ModernButton(nav_frame, text="Next ▶", command=lambda: next_image_handler(app),
                           bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=12, pady=6)
    next_btn.pack(side=tk.LEFT)
    
    # Jump to image
    jump_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
    jump_frame.pack(side=tk.LEFT, pady=12, padx=20)
    
    tk.Label(jump_frame, text="Go to:", bg=ModernColors.DARKER_BG, fg=ModernColors.TEXT_SECONDARY, 
            font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 8))
    
    app.jump_var = tk.StringVar() # Stored on app
    jump_entry = tk.Entry(jump_frame, textvariable=app.jump_var, width=8, 
                         font=('Segoe UI', 9), bg=ModernColors.CANVAS_BG, fg='#000000', bd=1)
    app.jump_entry_widget = jump_entry # Store for potential access in handler
    jump_entry.pack(side=tk.LEFT, padx=(0, 8))
    jump_entry.bind('<Return>', lambda event: jump_to_image_by_number_handler(app, event))
    
    jump_btn = ModernButton(jump_frame, text="Go", command=lambda: jump_to_image_by_number_handler(app),
                           bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), padx=10, pady=4)
    jump_btn.pack(side=tk.LEFT)
    
    # Zoom controls
    zoom_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
    zoom_frame.pack(side=tk.LEFT, pady=12, padx=20)
    
    ModernButton(zoom_frame, text="🔍+", command=lambda: zoom_in_handler(app),
                bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
    ModernButton(zoom_frame, text="🔍-", command=lambda: zoom_out_handler(app),
                bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
    ModernButton(zoom_frame, text="⌂", command=lambda: reset_zoom_handler(app),
                bg=ModernColors.BUTTON_SECONDARY, font=('Segoe UI', 9), width=4, pady=4).pack(side=tk.LEFT, padx=2)
    
    # Edit controls
    edit_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
    edit_frame.pack(side=tk.LEFT, pady=12, padx=20)
    
    ModernButton(edit_frame, text="📋 Copy", command=app.copy_annotation,
                bg='#28a745', hover_color='#34ce57', font=('Segoe UI', 9), padx=8, pady=4).pack(side=tk.LEFT, padx=2)
    ModernButton(edit_frame, text="📄 Paste", command=app.paste_annotation,
                bg='#ffc107', hover_color='#ffcd39', font=('Segoe UI', 9), padx=8, pady=4).pack(side=tk.LEFT, padx=2)
    
    # Visibility toggle
    toggle_frame = tk.Frame(controls_frame, bg=ModernColors.DARKER_BG)
    toggle_frame.pack(side=tk.RIGHT, pady=12, padx=15)
    
    app.visibility_btn = ModernButton(toggle_frame, text="👁️ Hide Boxes", 
                                      command=lambda: toggle_boxes_visibility_handler(app),
                                      bg='#6f42c1', hover_color='#8a63d2',
                                      font=('Segoe UI', 9), padx=12, pady=6)
    app.visibility_btn.pack()
    
    # Canvas container
    canvas_container = tk.Frame(parent_frame, bg=ModernColors.BORDER, bd=1, relief=tk.SOLID)
    canvas_container.pack(fill=tk.BOTH, expand=True)
    
    app.canvas = tk.Canvas(canvas_container, bg=ModernColors.CANVAS_BG, cursor="crosshair") # Stored on app
    
    # Scrollbars
    h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=app.canvas.xview)
    v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=app.canvas.yview)
    app.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
    
    app.canvas.grid(row=0, column=0, sticky="nsew")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    
    canvas_container.grid_rowconfigure(0, weight=1)
    canvas_container.grid_columnconfigure(0, weight=1)
    
    # Enhanced canvas events for editing
    app.canvas.bind("<Button-1>", app.on_canvas_click)
    app.canvas.bind("<B1-Motion>", app.on_canvas_drag)
    app.canvas.bind("<ButtonRelease-1>", app.on_canvas_release)
    app.canvas.bind("<Button-3>", app.on_right_click)
    app.canvas.bind("<B3-Motion>", app.on_pan)
    app.canvas.bind("<ButtonRelease-3>", app.end_pan)
    app.canvas.bind("<MouseWheel>", app.on_mousewheel)
    app.canvas.bind("<Motion>", app.on_mouse_motion)
    app.canvas.bind("<Double-Button-1>", app.on_double_click)


def create_enhanced_right_controls(parent_frame, app):
    """Create enhanced right sidebar with model annotation controls"""
    # Class input section
    class_frame = tk.LabelFrame(parent_frame, text=" 🏷️ Annotation Class ", 
                               bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                               font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
    class_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
    
    app.class_var = tk.StringVar(value=app.annotation_manager.current_class) # Stored on app
    class_entry = tk.Entry(class_frame, textvariable=app.class_var, 
                          font=('Segoe UI', 11), bg=ModernColors.CANVAS_BG, fg='#000000', 
                          bd=1, relief=tk.SOLID)
    class_entry.pack(fill=tk.X, padx=10, pady=(10, 5))
    class_entry.bind('<Return>', app.update_current_class)
    
    ModernButton(class_frame, text="✓ Update Class", command=app.update_current_class,
                bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                font=('Segoe UI', 9), pady=6).pack(fill=tk.X, padx=10, pady=(0, 10))
    
    # Model annotation review section
    app.review_frame = tk.LabelFrame(parent_frame, text=" 🤖 Model Annotation Review ", 
                                     bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                     font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
    app.review_frame.pack(fill=tk.X, padx=15, pady=10)
    app.review_frame.pack_forget()  # Hidden by default
    
    review_buttons = tk.Frame(app.review_frame, bg=ModernColors.SIDEBAR_BG)
    review_buttons.pack(fill=tk.X, padx=10, pady=10)
    
    ModernButton(review_buttons, text="✅ Approve All", command=app.approve_model_annotations,
                bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
    
    ModernButton(review_buttons, text="✏️ Edit & Approve", command=app.edit_model_annotations,
                bg=ModernColors.BUTTON_WARNING, hover_color='#e86900',
                font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
    
    ModernButton(review_buttons, text="❌ Reject All", command=app.reject_model_annotations,
                bg=ModernColors.BUTTON_DANGER, hover_color='#e74856',
                font=('Segoe UI', 9), pady=6).pack(fill=tk.X, pady=2)
    
    # Current annotations
    annotations_frame = tk.LabelFrame(parent_frame, text=" 📝 Current Annotations ", 
                                     bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                     font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
    annotations_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
    # Listbox container
    list_container = tk.Frame(annotations_frame, bg=ModernColors.SIDEBAR_BG)
    list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    app.annotations_listbox = tk.Listbox(list_container, bg=ModernColors.CANVAS_BG, # Stored on app
                                         fg='#000000', font=('Segoe UI', 9),
                                         selectbackground=ModernColors.ACCENT,
                                         bd=1, relief=tk.SOLID)
    list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", 
                                  command=app.annotations_listbox.yview)
    app.annotations_listbox.configure(yscrollcommand=list_scrollbar.set)
    
    app.annotations_listbox.pack(side="left", fill="both", expand=True)
    list_scrollbar.pack(side="right", fill="y")
    
    # Bind selection event
    app.annotations_listbox.bind('<<ListboxSelect>>', app.on_annotation_select)
    # Bind right-click for context menu
    app.annotations_listbox.bind('<Button-3>', lambda event: show_annotation_list_context_menu_handler(app, event)) # This line was already added
    
    # Annotation controls
    controls_container = tk.Frame(annotations_frame, bg=ModernColors.SIDEBAR_BG)
    controls_container.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    ModernButton(controls_container, text="🎨 Change Color", 
                command=app.change_annotation_color,
                bg=ModernColors.BUTTON_WARNING, hover_color='#e86900',
                font=('Segoe UI', 9), pady=5).pack(fill=tk.X, pady=2)
    
    ModernButton(controls_container, text="🗑️ Delete Selected", 
                command=app.delete_selected_annotation,
                bg=ModernColors.BUTTON_DANGER, hover_color='#e74856',
                font=('Segoe UI', 9), pady=5).pack(fill=tk.X, pady=2)
    
    # Action buttons
    action_frame = tk.LabelFrame(parent_frame, text=" ⚡ Actions ", 
                                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY, 
                                font=('Segoe UI', 10, 'bold'), bd=1, relief=tk.SOLID)
    action_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
    
    ModernButton(action_frame, text="💾 Update Annotations", command=app.update_annotations,
                bg=ModernColors.BUTTON_SUCCESS, hover_color='#16a085',
                font=('Segoe UI', 10, 'bold'), pady=8).pack(fill=tk.X, padx=10, pady=(10, 5))
    
    ModernButton(action_frame, text="👀 Preview Annotations", command=app.preview_annotations,
                bg=ModernColors.BUTTON_PRIMARY, hover_color=ModernColors.BUTTON_PRIMARY_HOVER,
                font=('Segoe UI', 10, 'bold'), pady=8).pack(fill=tk.X, padx=10, pady=(5, 10))

def create_status_bar(parent_frame, app):
    """Create bottom status bar"""
    status_frame = tk.Frame(parent_frame, bg=ModernColors.DARKER_BG, height=35)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
    status_frame.pack_propagate(False)
    
    app.status_bar = tk.Label(status_frame, text="Ready - Select a folder to begin", # Stored on app
                              bg=ModernColors.DARKER_BG, fg=ModernColors.TEXT_SECONDARY, 
                              font=('Segoe UI', 9), anchor=tk.W)
    app.status_bar.pack(fill=tk.BOTH, padx=15, pady=8)

# --- End of new UI creation functions ---
