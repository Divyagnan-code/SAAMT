def create_enhanced_sidebar(self, parent):
    """Create enhanced left sidebar with scrollable thumbnails"""
    # Header and navigation section
    header_frame = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG)
    header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    tk.Label(header_frame, text="📷 Images", bg=ModernColors.SIDEBAR_BG, fg=ModernColors.TEXT_PRIMARY,
            font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
    
    # Controls section
    controls_frame = tk.Frame(parent, bg=ModernColors.SIDEBAR_BG)
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
                          command=self.previous_image, 
                          font=('Segoe UI', 9), padx=10, pady=4)
    prev_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    next_btn = ModernButton(nav_buttons, text="Next ▶", 
                          command=self.next_image, 
                          font=('Segoe UI', 9), padx=10, pady=4)
    next_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
    
    # Visibility and annotation controls
    control_actions = tk.Frame(controls_frame, bg=ModernColors.SIDEBAR_BG)
    control_actions.pack(fill=tk.X, pady=(0, 5))
    
    # Visibility toggle button
    self.visibility_btn = ModernButton(control_actions, text="👁️ Hide Boxes", 
                                  command=self.toggle_boxes_visibility, 
                                  font=('Segoe UI', 9), padx=10, pady=4)
    self.visibility_btn.pack(fill=tk.X, pady=(0, 5))
    
    # Complete annotation button
    self.complete_btn = ModernButton(control_actions, text="✓ Complete Annotation", 
                                command=self.complete_current_annotation, 
                                bg=ModernColors.BUTTON_SUCCESS, 
                                hover_color='#12a530',
                                font=('Segoe UI', 9, 'bold'), padx=10, pady=4)
    self.complete_btn.pack(fill=tk.X)
    
    # Create notebook for tabs
    self.sidebar_notebook = ttk.Notebook(parent)
    self.sidebar_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Tab 1: All Images
    self.all_images_frame = tk.Frame(self.sidebar_notebook, bg=ModernColors.SIDEBAR_BG)
    self.sidebar_notebook.add(self.all_images_frame, text="All Images")
    
    # Tab 2: Annotated Images
    self.annotated_images_frame = tk.Frame(self.sidebar_notebook, bg=ModernColors.SIDEBAR_BG)
    self.sidebar_notebook.add(self.annotated_images_frame, text="Annotated Images")
    
    # Setup "All Images" tab content
    all_header = tk.Frame(self.all_images_frame, bg=ModernColors.SIDEBAR_BG)
    all_header.pack(fill=tk.X, padx=5, pady=5)
    
    # Load more button for all images
    self.load_more_btn = ModernButton(all_header, text="Load More", 
                                  command=self.load_more_thumbnails, 
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
    
    # Setup "Annotated Images" tab content
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
    
    # Enhanced mousewheel scrolling for both tabs
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
