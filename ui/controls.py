import tkinter as tk
from tkinter import ttk, colorchooser

from .styles import ModernColors, ModernButton

class ControlPanel:
    """Right-side annotation controls panel"""
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app = app_controller
        
        # Create right sidebar frame
        self.controls_frame = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG, width=300)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=0, pady=0)
        self.controls_frame.pack_propagate(False)  # Don't shrink
        
        # Create sections
        self.create_header()
        self.create_annotation_details()
        self.create_statistics_section()
        self.create_help_section()
    
    def create_header(self):
        """Create controls header"""
        header_frame = tk.Frame(self.controls_frame, bg=ModernColors.SIDEBAR_BG)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(header_frame, text="✏️ Annotation Tools", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
    
    def create_annotation_details(self):
        """Create annotation details section"""
        details_frame = tk.LabelFrame(self.controls_frame, text="Selected Annotation", 
                                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                    font=('Segoe UI', 10))
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # No annotation selected initially
        self.no_selection_label = tk.Label(details_frame, 
                                         text="No annotation selected", 
                                         bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                                         font=('Segoe UI', 9))
        self.no_selection_label.pack(pady=10)
        
        # Details container (initially hidden)
        self.details_container = tk.Frame(details_frame, bg=ModernColors.SIDEBAR_BG)
        
        # Class edit
        class_frame = tk.Frame(self.details_container, bg=ModernColors.SIDEBAR_BG)
        class_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(class_frame, text="Class:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.selected_class_var = tk.StringVar()
        self.selected_class_combo = ttk.Combobox(class_frame, 
                                               textvariable=self.selected_class_var,
                                               width=15,
                                               style='Modern.TCombobox')
        self.selected_class_combo['values'] = ('person', 'car', 'bike', 'truck', 'traffic light', 'stop sign')
        self.selected_class_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.selected_class_combo.bind("<<ComboboxSelected>>", self.on_selected_class_changed)
        self.selected_class_combo.bind("<Return>", self.on_selected_class_changed)
        
        # Coordinates
        coords_frame = tk.Frame(self.details_container, bg=ModernColors.SIDEBAR_BG)
        coords_frame.pack(fill=tk.X, pady=5)
        
        # X1, Y1
        tk.Label(coords_frame, text="X1:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).grid(row=0, column=0, sticky="e", padx=(0, 5))
        
        self.x1_var = tk.StringVar()
        x1_entry = ttk.Entry(coords_frame, textvariable=self.x1_var, width=6, style='Modern.TEntry')
        x1_entry.grid(row=0, column=1, padx=(0, 10))
        
        tk.Label(coords_frame, text="Y1:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).grid(row=0, column=2, sticky="e", padx=(0, 5))
        
        self.y1_var = tk.StringVar()
        y1_entry = ttk.Entry(coords_frame, textvariable=self.y1_var, width=6, style='Modern.TEntry')
        y1_entry.grid(row=0, column=3)
        
        # X2, Y2
        tk.Label(coords_frame, text="X2:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).grid(row=1, column=0, sticky="e", padx=(0, 5), pady=(5, 0))
        
        self.x2_var = tk.StringVar()
        x2_entry = ttk.Entry(coords_frame, textvariable=self.x2_var, width=6, style='Modern.TEntry')
        x2_entry.grid(row=1, column=1, padx=(0, 10), pady=(5, 0))
        
        tk.Label(coords_frame, text="Y2:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).grid(row=1, column=2, sticky="e", padx=(0, 5), pady=(5, 0))
        
        self.y2_var = tk.StringVar()
        y2_entry = ttk.Entry(coords_frame, textvariable=self.y2_var, width=6, style='Modern.TEntry')
        y2_entry.grid(row=1, column=3, pady=(5, 0))
        
        # Update coordinates button
        update_coords_btn = ModernButton(self.details_container, text="Update Coordinates", 
                                       command=self.on_update_coordinates,
                                       font=('Segoe UI', 9), padx=10, pady=4)
        update_coords_btn.pack(fill=tk.X, pady=5)
        
        # Color picker
        color_frame = tk.Frame(self.details_container, bg=ModernColors.SIDEBAR_BG)
        color_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(color_frame, text="Color:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.color_preview = tk.Canvas(color_frame, width=30, height=20, bg=ModernColors.ACCENT, bd=1, relief=tk.SOLID)
        self.color_preview.pack(side=tk.LEFT, padx=(0, 5))
        
        color_pick_btn = ModernButton(color_frame, text="Choose Color", 
                                     command=self.on_choose_color,
                                     font=('Segoe UI', 8), padx=5, pady=2)
        color_pick_btn.pack(side=tk.LEFT)
        
        # Action buttons
        actions_frame = tk.Frame(self.details_container, bg=ModernColors.SIDEBAR_BG)
        actions_frame.pack(fill=tk.X, pady=5)
        
        copy_btn = ModernButton(actions_frame, text="📋 Copy", 
                               command=self.app.copy_selected_annotation,
                               font=('Segoe UI', 9), padx=5, pady=4)
        copy_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        delete_btn = ModernButton(actions_frame, text="🗑️ Delete", 
                                 command=self.app.delete_selected_annotation,
                                 bg=ModernColors.BUTTON_DANGER,
                                 font=('Segoe UI', 9), padx=5, pady=4)
        delete_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def create_statistics_section(self):
        """Create statistics section"""
        stats_frame = tk.LabelFrame(self.controls_frame, text="Statistics", 
                                  bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                  font=('Segoe UI', 10))
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Image info
        image_info_frame = tk.Frame(stats_frame, bg=ModernColors.SIDEBAR_BG)
        image_info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(image_info_frame, text="Image:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        
        self.image_name_var = tk.StringVar(value="No image loaded")
        tk.Label(image_info_frame, textvariable=self.image_name_var, 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                font=('Segoe UI', 9)).grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        tk.Label(image_info_frame, text="Dimensions:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        self.image_dims_var = tk.StringVar(value="-")
        tk.Label(image_info_frame, textvariable=self.image_dims_var, 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                font=('Segoe UI', 9)).grid(row=1, column=1, sticky="w", padx=(5, 0), pady=(5, 0))
        
        # Annotation stats
        annotation_stats_frame = tk.Frame(stats_frame, bg=ModernColors.SIDEBAR_BG)
        annotation_stats_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(annotation_stats_frame, text="Total Annotations:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        
        self.total_annotations_var = tk.StringVar(value="0")
        tk.Label(annotation_stats_frame, textvariable=self.total_annotations_var, 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                font=('Segoe UI', 9)).grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        tk.Label(annotation_stats_frame, text="Annotated Images:", 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        self.annotated_images_var = tk.StringVar(value="0")
        tk.Label(annotation_stats_frame, textvariable=self.annotated_images_var, 
                bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                font=('Segoe UI', 9)).grid(row=1, column=1, sticky="w", padx=(5, 0), pady=(5, 0))
    
    def create_help_section(self):
        """Create help section with keyboard shortcuts"""
        help_frame = tk.LabelFrame(self.controls_frame, text="Keyboard Shortcuts", 
                                 bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
                                 font=('Segoe UI', 10))
        help_frame.pack(fill=tk.X, padx=10, pady=5)
        
        shortcuts = [
            ("Ctrl+S", "Save annotations"),
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y", "Redo"),
            ("Ctrl+C", "Copy annotation"),
            ("Ctrl+V", "Paste annotation"),
            ("Delete", "Delete selected"),
            ("Space", "Toggle box visibility"),
            ("Ctrl+0", "Reset zoom"),
            ("Ctrl++", "Zoom in"),
            ("Ctrl+-", "Zoom out"),
            ("Left/Right", "Previous/Next image")
        ]
        
        for i, (key, desc) in enumerate(shortcuts):
            tk.Label(help_frame, text=key, 
                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.ACCENT,
                    font=('Segoe UI', 9, 'bold')).grid(row=i, column=0, sticky="w", pady=(2, 0))
            
            tk.Label(help_frame, text=desc, 
                    bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_SECONDARY,
                    font=('Segoe UI', 9)).grid(row=i, column=1, sticky="w", padx=(5, 0), pady=(2, 0))
    
    def show_annotation_details(self, annotation):
        """Show details for the selected annotation"""
        if not annotation:
            self.no_selection_label.pack(pady=10)
            self.details_container.pack_forget()
            return
        
        # Hide 'no selection' label and show details
        self.no_selection_label.pack_forget()
        self.details_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Update controls with annotation data
        self.selected_class_var.set(annotation.get('class', ''))
        
        # Update coordinates
        if 'bbox' in annotation:
            x1, y1, x2, y2 = annotation['bbox']
            self.x1_var.set(str(int(x1)))
            self.y1_var.set(str(int(y1)))
            self.x2_var.set(str(int(x2)))
            self.y2_var.set(str(int(y2)))
        
        # Update color preview
        color = annotation.get('color', ModernColors.ACCENT)
        self.color_preview.config(bg=color)
        self.color_preview.update()
    
    def hide_annotation_details(self):
        """Hide annotation details"""
        self.no_selection_label.pack(pady=10)
        self.details_container.pack_forget()
    
    def update_image_info(self, image_name, width, height):
        """Update image information"""
        if image_name:
            self.image_name_var.set(image_name)
            self.image_dims_var.set(f"{width} × {height} px")
        else:
            self.image_name_var.set("No image loaded")
            self.image_dims_var.set("-")
    
    def update_statistics(self, total_annotations, annotated_images_count):
        """Update annotation statistics"""
        self.total_annotations_var.set(str(total_annotations))
        self.annotated_images_var.set(f"{annotated_images_count}")
    
    def on_selected_class_changed(self, event=None):
        """Handle selected annotation class change"""
        new_class = self.selected_class_var.get()
        self.app.update_selected_annotation_class(new_class)
    
    def on_update_coordinates(self):
        """Handle coordinate update button click"""
        try:
            x1 = int(self.x1_var.get())
            y1 = int(self.y1_var.get())
            x2 = int(self.x2_var.get())
            y2 = int(self.y2_var.get())
            
            self.app.update_selected_annotation_coords(x1, y1, x2, y2)
        except ValueError:
            # Handle invalid input
            pass
    
    def on_choose_color(self):
        """Handle color picker button click"""
        current_color = self.color_preview.cget("bg")
        color = colorchooser.askcolor(color=current_color, title="Choose Annotation Color")
        
        if color[1]:  # If a color was chosen (not canceled)
            self.color_preview.config(bg=color[1])
            self.app.update_selected_annotation_color(color[1])
