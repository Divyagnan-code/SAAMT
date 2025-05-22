import tkinter as tk
from tkinter import ttk, filedialog

from .styles import ModernColors, ModernButton

class Toolbar:
    """Enhanced toolbar with model controls"""
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app = app_controller
        
        # Create toolbar frame
        self.toolbar_frame = tk.Frame(parent, bg=ModernColors.DARKER_BG, height=50)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # File operations section
        self.create_file_section()
        
        # Model section
        self.create_model_section()
        
        # Tool section
        self.create_tool_section()
        
        # Class selection section
        self.create_class_section()
        
        # Progress bar for loading
        self.create_progress_section()
    
    def create_file_section(self):
        """Create file operations section"""
        file_frame = tk.Frame(self.toolbar_frame, bg=ModernColors.DARKER_BG)
        file_frame.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.Y)
        
        # Open folder button
        open_btn = ModernButton(file_frame, text="📂 Open Folder", 
                              command=self.app.open_folder, 
                              font=('Segoe UI', 10))
        open_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save annotations button
        save_btn = ModernButton(file_frame, text="💾 Save", 
                              command=self.app.save_annotations, 
                              bg=ModernColors.BUTTON_PRIMARY,
                              font=('Segoe UI', 10))
        save_btn.pack(side=tk.LEFT, padx=5)
    
    def create_model_section(self):
        """Create model controls section"""
        model_frame = tk.Frame(self.toolbar_frame, bg=ModernColors.DARKER_BG)
        model_frame.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.Y)
        
        # Model selection
        model_label = tk.Label(model_frame, text="Model:", 
                             bg=ModernColors.DARKER_BG, 
                             fg=ModernColors.TEXT_PRIMARY,
                             font=('Segoe UI', 10))
        model_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Model combobox
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, 
                                      textvariable=self.model_var,
                                      width=15, 
                                      state="readonly",
                                      style='Modern.TCombobox')
        self.model_combo.pack(side=tk.LEFT)
        self.model_combo.bind("<<ComboboxSelected>>", self.app.on_model_selected)
        
        # Confidence threshold
        threshold_frame = tk.Frame(model_frame, bg=ModernColors.DARKER_BG)
        threshold_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        threshold_label = tk.Label(threshold_frame, text="Confidence:", 
                                  bg=ModernColors.DARKER_BG, 
                                  fg=ModernColors.TEXT_PRIMARY,
                                  font=('Segoe UI', 10))
        threshold_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.threshold_var = tk.DoubleVar(value=0.5)
        threshold_scale = ttk.Scale(threshold_frame, 
                                   from_=0.1, to=0.9, 
                                   orient=tk.HORIZONTAL,
                                   variable=self.threshold_var,
                                   length=100,
                                   style='Modern.Horizontal.TScale')
        threshold_scale.pack(side=tk.LEFT)
        threshold_scale.bind("<ButtonRelease-1>", self.app.on_threshold_changed)
        
        self.threshold_value_label = tk.Label(threshold_frame, 
                                           text="0.50", 
                                           bg=ModernColors.DARKER_BG, 
                                           fg=ModernColors.TEXT_PRIMARY,
                                           font=('Segoe UI', 9),
                                           width=4)
        self.threshold_value_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Run model button
        self.run_model_btn = ModernButton(model_frame, text="🔍 Detect Objects", 
                                        command=self.app.run_model, 
                                        bg=ModernColors.BUTTON_SUCCESS,
                                        font=('Segoe UI', 10))
        self.run_model_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_tool_section(self):
        """Create annotation tools section"""
        tool_frame = tk.Frame(self.toolbar_frame, bg=ModernColors.DARKER_BG)
        tool_frame.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.Y)
        
        # Separator
        separator = ttk.Separator(tool_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Annotation tools
        self.draw_btn = ModernButton(tool_frame, text="✏️ Draw Box", 
                                   command=lambda: self.app.set_mode('draw'), 
                                   bg=ModernColors.BUTTON_PRIMARY,
                                   font=('Segoe UI', 10))
        self.draw_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_btn = ModernButton(tool_frame, text="🔄 Edit Box", 
                                   command=lambda: self.app.set_mode('edit'), 
                                   bg=ModernColors.BUTTON_SECONDARY,
                                   font=('Segoe UI', 10))
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = ModernButton(tool_frame, text="🗑️ Delete", 
                                     command=self.app.delete_selected_annotation, 
                                     bg=ModernColors.BUTTON_WARNING,
                                     font=('Segoe UI', 10))
        self.delete_btn.pack(side=tk.LEFT, padx=5)
    
    def create_class_section(self):
        """Create class selection section"""
        class_frame = tk.Frame(self.toolbar_frame, bg=ModernColors.DARKER_BG)
        class_frame.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.Y)
        
        # Separator
        separator = ttk.Separator(class_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Class selection
        class_label = tk.Label(class_frame, text="Class:", 
                             bg=ModernColors.DARKER_BG, 
                             fg=ModernColors.TEXT_PRIMARY,
                             font=('Segoe UI', 10))
        class_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Class combobox with entry
        self.class_var = tk.StringVar(value="person")
        self.class_combo = ttk.Combobox(class_frame, 
                                      textvariable=self.class_var,
                                      width=12,
                                      style='Modern.TCombobox')
        self.class_combo['values'] = ('person', 'car', 'bike', 'truck', 'traffic light', 'stop sign')
        self.class_combo.pack(side=tk.LEFT)
        self.class_combo.bind("<<ComboboxSelected>>", self.app.on_class_selected)
        self.class_combo.bind("<Return>", self.app.on_class_entered)
    
    def create_progress_section(self):
        """Create progress bar section (initially hidden)"""
        self.progress_frame = tk.Frame(self.toolbar_frame, bg=ModernColors.DARKER_BG, height=48)
        # Not packed initially - will be shown when needed
        
        progress_label = tk.Label(self.progress_frame, text="Loading images...", 
                                 bg=ModernColors.DARKER_BG, fg=ModernColors.TEXT_PRIMARY,
                                 font=('Segoe UI', 10))
        progress_label.pack(side=tk.LEFT, padx=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, 
                                          orient=tk.HORIZONTAL, 
                                          length=300, 
                                          mode='indeterminate',
                                          style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(side=tk.LEFT, padx=5, pady=10)
    
    def show_progress(self):
        """Show the progress bar"""
        self.progress_frame.pack(fill=tk.BOTH, expand=True)
        self.progress_bar.start(10)  # Start animation
    
    def hide_progress(self):
        """Hide the progress bar"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
    
    def update_model_list(self, models):
        """Update the model dropdown list"""
        if not models:
            self.model_combo['values'] = ['<No Models Available>']
            self.model_var.set('<No Models Available>')
            self.run_model_btn.configure(state=tk.DISABLED)
        else:
            self.model_combo['values'] = models
            self.model_var.set(models[0])
            self.run_model_btn.configure(state=tk.NORMAL)
    
    def update_threshold_display(self, value):
        """Update the threshold value display"""
        self.threshold_value_label.configure(text=f"{value:.2f}")
    
    def update_tool_buttons(self, mode):
        """Update the tool buttons based on current mode"""
        if mode == 'draw':
            self.draw_btn.configure(bg=ModernColors.BUTTON_PRIMARY)
            self.edit_btn.configure(bg=ModernColors.BUTTON_SECONDARY)
        elif mode == 'edit':
            self.draw_btn.configure(bg=ModernColors.BUTTON_SECONDARY)
            self.edit_btn.configure(bg=ModernColors.BUTTON_PRIMARY)
