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
from auto_annotator import ModelManager
from ui_components import (ModernColors, ModernButton,
                           create_enhanced_toolbar, create_enhanced_sidebar,
                           create_enhanced_canvas_area, create_enhanced_right_controls,
                           create_status_bar)
from utils import UndoRedoManager
from annotation_manager import AnnotationManager
from event_handlers import ( # Import new handlers
    select_folder_handler, previous_image_handler, next_image_handler,
    zoom_in_handler, zoom_out_handler, reset_zoom_handler,
    try_model_handler, train_model_handler, on_mode_change_handler,
    on_model_change_handler, on_confidence_change_handler,
    jump_to_image_by_number_handler, toggle_boxes_visibility_handler
)

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
        self.annotation_manager = AnnotationManager()
        
        # Data structures
        self.images_folder = ""
        self.image_files = []
        self.annotated_images = set()  # Set to keep track of images with completed annotations
        self.current_image_index = 0
        self.current_image = None
        self.photo_image = None
        
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
        create_enhanced_toolbar(toolbar_frame, self) # Use imported function
        
        # Content section
        content_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(content_paned, weight=1)
        self.paned_windows['content'] = content_paned
        
        # Left sidebar
        left_frame = tk.Frame(content_paned, bg=ModernColors.SIDEBAR_BG, width=250)
        content_paned.add(left_frame, weight=0)
        create_enhanced_sidebar(left_frame, self) # Use imported function
        
        # Center canvas area
        center_frame = tk.Frame(content_paned, bg=ModernColors.DARK_BG)
        content_paned.add(center_frame, weight=2)
        create_enhanced_canvas_area(center_frame, self) # Use imported function
        
        # Right controls
        right_frame = tk.Frame(content_paned, bg=ModernColors.SIDEBAR_BG, width=300)
        content_paned.add(right_frame, weight=0)
        create_enhanced_right_controls(right_frame, self) # Use imported function
        
        # Status bar
        create_status_bar(main_frame, self) # Use imported function
    
    # Removed create_enhanced_toolbar, create_enhanced_sidebar, 
    # create_enhanced_canvas_area, create_enhanced_right_controls, 
    # and create_status_bar method definitions from here.
    
    def save_initial_state(self):
        """Save initial state for undo/redo"""
        self.undo_manager.save_state({
            'temp_annotations': [], # Managed by annotation_manager, but snapshot for undo needed
            'current_image_index': 0
        })
    
    def save_state_for_undo(self):
        """Save current state for undo/redo"""
        state = {
            'temp_annotations': copy.deepcopy(self.annotation_manager.temp_annotations),
            'current_image_index': self.current_image_index
        }
        self.undo_manager.save_state(state)
    
    def undo_action(self):
        """Undo last action"""
        state = self.undo_manager.undo()
        if state:
            self.annotation_manager.temp_annotations = state['temp_annotations']
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("↶ Undo completed")
    
    def redo_action(self):
        """Redo last undone action"""
        state = self.undo_manager.redo()
        if state:
            self.annotation_manager.temp_annotations = state['temp_annotations']
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("↷ Redo completed")
    
    # Removed on_mode_change, on_model_change, on_confidence_change
    # Their logic is now in event_handlers.py and called from ui_components.py
    
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
            predictions = self.model_manager.predict(image_path, self.annotation_manager.current_class, prompt=None, anti_prompt=None)
            
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
                    predictions = self.model_manager.predict(image_path, self.annotation_manager.current_class, prompt=None, anti_prompt=None)
                    
                    if predictions:
                        if auto_approve:
                            # Auto-approve high confidence annotations
                            high_conf_annotations = [ann for ann in predictions if ann.get('confidence', 0) > 0.9]
                            if high_conf_annotations:
                                # Convert model annotations to regular annotations
                                for ann_model in high_conf_annotations: # Renamed to avoid conflict
                                    ann_model.pop('is_model_annotation', None)
                                    ann_model.pop('confidence', None)
                                    if 'color' not in ann_model:
                                        ann_model['color'] = self.annotation_manager.annotation_colors[approved % len(self.annotation_manager.annotation_colors)]
                                
                                self.annotation_manager.annotations[image_name] = high_conf_annotations
                                approved += len(high_conf_annotations)
                        else:
                            # Save for manual review
                            self.annotation_manager.annotations[image_name + "_model_pending"] = predictions
                
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
        self.annotation_manager.save_annotations(self.images_folder)
        
        message = f"Batch annotation completed!\n\nProcessed: {processed} images"
        if approved > 0:
            message += f"\nAuto-approved: {approved} annotations"
        
        messagebox.showinfo("Batch Complete", message)
        self.update_status("Batch annotation completed")
    
    def approve_model_annotations(self):
        """Approve all model annotations"""
        if self.model_annotations:
            self.save_state_for_undo()
            
            # Convert model annotations to regular annotations by AnnotationManager
            num_approved = self.annotation_manager.approve_model_annotations(self.model_annotations)
            self.model_annotations = [] # Clear model specific annotations in AnnotationTool
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
        """Copy selected annotation using AnnotationManager."""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if self.annotation_manager.copy_annotation(idx):
                self.update_status("📋 Annotation copied")
            else:
                messagebox.showwarning("Copy Error", "Failed to copy annotation.")
        else:
            messagebox.showwarning("No Selection", "Please select an annotation to copy.")

    def paste_annotation(self):
        """Paste last copied annotation using AnnotationManager."""
        if self.current_image and self.annotation_manager.last_copied_annotation:
            self.save_state_for_undo()
            img_width, img_height = self.current_image.size
            
            new_annotation = self.annotation_manager.paste_annotation(img_width, img_height)
            
            if new_annotation:
                self.display_image_on_canvas()
                self.update_annotations_list()
                self.update_status("📄 Annotation pasted")
            else:
                messagebox.showwarning("Paste Error", "Failed to paste annotation.")
        else:
            messagebox.showwarning("Nothing to Paste", "No annotation copied or no image loaded.")

    def on_annotation_select(self, event=None):
        """Handle annotation selection from listbox"""
        selection = self.annotations_listbox.curselection()
        if selection and selection[0] < len(self.annotation_manager.temp_annotations): # Use manager's temp_annotations
            self.selected_annotation = selection[0]
            self.display_image_on_canvas()  # Refresh display to show selection

    def get_annotation_at_point(self, x, y):
        """Get annotation index at given canvas coordinates using AnnotationManager for temp_annotations."""
        # Model annotations are still managed by AnnotationTool for now, so check them here.
        img_x_model = (x - self.pan_x) / self.zoom_factor
        img_y_model = (y - self.pan_y) / self.zoom_factor
        for i in reversed(range(len(self.model_annotations))):
            ann = self.model_annotations[i]
            bbox = ann['bbox']
            if (bbox[0] <= img_x_model <= bbox[2] and bbox[1] <= img_y_model <= bbox[3]):
                return f"model_{i}" # Distinguish model annotation
        
        # Check temporary annotations via AnnotationManager
        # AnnotationManager's get_temp_annotation_at_point expects canvas coords, but here we pass image coords
        # For consistency, let AnnotationTool continue to convert coords and pass them if needed,
        # or adapt AnnotationManager. For now, we'll use the existing logic structure.
        idx = self.annotation_manager.get_temp_annotation_at_point(x, y, self.zoom_factor, self.pan_x, self.pan_y)
        if idx is not None:
            return idx
            
        return None
    
    def get_resize_handle_at_point(self, x, y, annotation_idx):
        """Get resize handle at given point for annotation"""
        if annotation_idx is None or isinstance(annotation_idx, str):
            return None
        
        # Ensure the index is valid for temp_annotations in AnnotationManager
        if annotation_idx >= len(self.annotation_manager.temp_annotations):
            return None
        
        bbox = self.annotation_manager.temp_annotations[annotation_idx]['bbox']
        
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
        """Handle annotation editing (move/resize) using AnnotationManager."""
        if self.selected_annotation is None or self.selected_annotation >= len(self.annotation_manager.temp_annotations):
            return

        img_width, img_height = self.current_image.size if self.current_image else (0,0)
        
        # Calculate change in image coordinates
        img_dx = (canvas_x - self.start_x) / self.zoom_factor
        img_dy = (canvas_y - self.start_y) / self.zoom_factor

        if self.selected_handle == "move":
            self.annotation_manager.move_temp_annotation_bbox(self.selected_annotation, img_dx, img_dy, img_width, img_height)
        else:
            # For resize, determine which part of the bbox is changing
            bbox_part_update = {}
            current_bbox = self.annotation_manager.temp_annotations[self.selected_annotation]['bbox']
            if 'n' in self.selected_handle: bbox_part_update['y1'] = current_bbox[1] + img_dy
            if 's' in self.selected_handle: bbox_part_update['y2'] = current_bbox[3] + img_dy
            if 'w' in self.selected_handle: bbox_part_update['x1'] = current_bbox[0] + img_dx
            if 'e' in self.selected_handle: bbox_part_update['x2'] = current_bbox[2] + img_dx
            
            self.annotation_manager.edit_temp_annotation_bbox(self.selected_annotation, bbox_part_update, img_width, img_height)

        self.start_x = canvas_x # Update start for next drag segment
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
        """Change annotation color by index using AnnotationManager."""
        if 0 <= idx < len(self.annotation_manager.temp_annotations):
            color = colorchooser.askcolor(title="Choose annotation color")[1]
            if color:
                if self.annotation_manager.change_temp_annotation_color(idx, color):
                    self.display_image_on_canvas()
                    self.update_status(f"Color changed for annotation {idx+1}")
                else:
                    messagebox.showerror("Error", "Failed to change color.")
    
    def copy_annotation_by_index(self, idx):
        """Copy annotation by index using AnnotationManager."""
        if self.annotation_manager.copy_annotation(idx):
            self.update_status("📋 Annotation copied")
        else:
            messagebox.showwarning("Copy Error", "Could not copy selected annotation.")

    def delete_annotation_by_index(self, idx):
        """Delete annotation by index using AnnotationManager."""
        if self.annotation_manager.delete_temp_annotation(idx):
            self.save_state_for_undo() # Save state after successful deletion
            self.display_image_on_canvas()
            self.update_annotations_list()
            self.update_status("🗑️ Annotation deleted")
        else:
            messagebox.showwarning("Delete Error", "Could not delete selected annotation.")
    
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
        """Edit annotation class using AnnotationManager."""
        if 0 <= annotation_idx < len(self.annotation_manager.temp_annotations):
            current_class_val = self.annotation_manager.temp_annotations[annotation_idx]['class']
            
            new_class = tk.simpledialog.askstring("Edit Class", 
                                                 f"Current class: {current_class_val}\nEnter new class:",
                                                 initialvalue=current_class_val)
            
            if new_class and new_class.strip():
                if self.annotation_manager.update_temp_annotation_class(annotation_idx, new_class.strip()):
                    self.save_state_for_undo() # Save state after successful update
                    self.display_image_on_canvas()
                    self.update_annotations_list()
                    self.update_status(f"✏️ Class changed to '{new_class.strip()}'")
                else:
                    messagebox.showerror("Error", "Failed to update class.")
    
    # select_folder is now select_folder_handler in event_handlers.py
    # load_images and its helpers remain in AnnotationTool due to complexity
    
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
            
            self.annotation_manager.load_existing_annotations(self.images_folder)
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
        # Prevent re-entry if already loading, unless it's the very first call (current_batch_start == 0 helps here)
        if self.loading_thumbnails and self.current_batch_start != 0: 
            return

        self.loading_thumbnails = True # Mark that thumbnail loading process has started
        
        if self.current_batch_start == 0: # If it's the very first load for this dataset
            for widget in self.thumb_scrollable_frame.winfo_children():
                widget.destroy() # Clear previous thumbnails
        
        # Visibility of load_more_btn will be managed by _on_thumbnails_loaded.
        # No need to manage it here directly before the first batch is even attempted.
        
        self.load_thumbnail_batch()
    
    def load_thumbnail_batch(self):
        """Prepare and start asynchronous loading of a thumbnail batch."""
        if not self.image_files or self.current_batch_start >= len(self.image_files):
            self.loading_thumbnails = False # All images are loaded or no images to load
            if hasattr(self, 'load_more_btn'):
                self.load_more_btn.pack_forget()
            return
        
        # Set loading_thumbnails to True only when a batch is actually being loaded.
        self.loading_thumbnails = True 
        
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
                                  relief=tk.SOLID, bd=1) # Default border
            
            # Determine status and visual cues
            image_file_name = thumb_data['file']
            ann_count = 0
            if image_file_name in self.annotation_manager.annotations:
                ann_count = len(self.annotation_manager.annotations[image_file_name])

            status_text = ""
            status_color = ModernColors.TEXT_SECONDARY # Default color
            frame_border_color = ModernColors.BORDER # Default border color for frame

            if image_file_name in self.annotated_images:
                status_text = "✅ Completed"
                status_color = ModernColors.BUTTON_SUCCESS 
                frame_border_color = ModernColors.BUTTON_SUCCESS # Highlight border for completed
                thumb_frame.configure(highlightbackground=frame_border_color, highlightthickness=2, bd=0)
            elif ann_count > 0:
                status_text = f"📝 {ann_count} annotations (In Progress)"
                status_color = ModernColors.ACCENT
                # Keep default frame border or specific color for in-progress if desired
            else:
                status_text = "⚪ No annotations"
                status_color = ModernColors.TEXT_SECONDARY
                # Keep default frame border

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
            
            # Annotation count - already determined above for status_text and color logic
            # status_text is already set.
            status_label = tk.Label(info_frame, text=status_text,
                                   bg=ModernColors.SIDEBAR_BG, 
                                   fg=status_color, # Use determined status_color
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
        
        self.current_batch_start += len(loaded_thumbnails) # Keep only one increment
        
        # Update scroll region
        self.thumb_canvas.update_idletasks()
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))

        # Manage "Load More" button visibility
        if self.current_batch_start >= len(self.image_files):
            if hasattr(self, 'load_more_btn'): # Check if button exists
                self.load_more_btn.pack_forget()
        else:
            if hasattr(self, 'load_more_btn'): # Check if button exists
                 # Ensure button is visible if there are more images.
                 # It should be packed in its parent (header_frame) correctly by create_enhanced_sidebar.
                 # Re-packing might be needed if it was forgotten.
                self.load_more_btn.pack(side=tk.RIGHT) 
        
        self.loading_thumbnails = False # Finished processing this batch, ready for next trigger.
    
    def load_more_thumbnails(self):
        """Command for the 'Load More' button."""
        if not self.loading_thumbnails and self.current_batch_start < len(self.image_files):
            # load_thumbnail_batch will set self.loading_thumbnails = True if it proceeds
            self.load_thumbnail_batch()
    
    def jump_to_image(self, index):
        """Jump to specific image"""
        if 0 <= index < len(self.image_files):
            self.current_image_index = index
            self.load_current_image()
    
    # jump_to_image_by_number is now jump_to_image_by_number_handler in event_handlers.py
    
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
        
        # Draw saved annotations (already part of temp_annotations if current image matches)
        # current_image_name = self.image_files[self.current_image_index]
        # if current_image_name in self.annotation_manager.annotations:
        #     for i, ann in enumerate(self.annotation_manager.annotations[current_image_name]):
        #         if ann.get('visible', True): # this logic might be redundant if temp_annotations is authoritative
        #             self.draw_bbox(ann['bbox'], ann['color'], ann['class'], 
        #                          selected=(i == self.selected_annotation and not self.reviewing_model_annotations)) # Avoid double selection highlight
        
        # Draw temporary annotations from AnnotationManager
        for i, ann in enumerate(self.annotation_manager.temp_annotations):
            if ann.get('visible', True):
                self.draw_bbox(ann['bbox'], ann['color'], ann['class'], 
                             selected=(i == self.selected_annotation))
        
        # Draw model annotations (still managed by AnnotationTool)
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
            
            current_class = self.annotation_manager.current_class
            color = self.annotation_manager.get_next_color()
            bbox_coords = [int(x1), int(y1), int(x2), int(y2)]
            
            self.annotation_manager.add_temp_annotation(bbox_coords, current_class, color)
            
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
            
    # Removed toggle_boxes_visibility, its logic is in toggle_boxes_visibility_handler
    
    def update_current_class(self, event=None):
        """Update current class in AnnotationManager."""
        new_class = self.class_var.get().strip()
        if new_class:
            self.annotation_manager.current_class = new_class
            self.update_status(f"Current class: {self.annotation_manager.current_class}")

    def load_temp_annotations(self): # Wrapper in AnnotationTool
        """Load temporary annotations for current image using AnnotationManager."""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return
        current_image_name = self.image_files[self.current_image_index]
        self.annotation_manager.load_temp_annotations(current_image_name)
        self.update_annotations_list() # UI update remains in AnnotationTool

    def update_annotations_list(self):
        """Update annotations listbox from AnnotationManager's temp_annotations."""
        self.annotations_listbox.delete(0, tk.END)
        for i, ann in enumerate(self.annotation_manager.temp_annotations): # Use manager's temp_annotations
            status = "👁️" if ann.get('visible', True) else "🔒"
            bbox_str = f"[{ann['bbox'][0]},{ann['bbox'][1]},{ann['bbox'][2]},{ann['bbox'][3]}]"
            model_indicator = " 🤖" if ann.get('is_model_annotation') else "" # is_model_annotation might need to be handled by AM
            self.annotations_listbox.insert(tk.END, f"{status} {ann['class']}: {bbox_str}{model_indicator}")

    def change_annotation_color(self):
        """Change annotation color using AnnotationManager."""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            # Ensure index is valid for manager's temp_annotations
            if 0 <= idx < len(self.annotation_manager.temp_annotations):
                color = colorchooser.askcolor(title="Choose annotation color")[1]
                if color:
                    if self.annotation_manager.change_temp_annotation_color(idx, color):
                        self.display_image_on_canvas()
                        self.update_status("Color changed.")
                    else:
                        messagebox.showerror("Error", "Failed to change color via manager.")
            else:
                messagebox.showwarning("Selection Error", "Invalid annotation selected.")

    def delete_selected_annotation(self):
        """Delete selected annotation using AnnotationManager."""
        selection = self.annotations_listbox.curselection()
        if selection:
            idx = selection[0]
            if self.annotation_manager.delete_temp_annotation(idx):
                self.save_state_for_undo() # Save state after successful deletion
                self.display_image_on_canvas()
                self.update_annotations_list()
                self.update_status("Annotation deleted.")
            else:
                messagebox.showerror("Delete Error", "Failed to delete annotation via manager.")
        else:
            messagebox.showwarning("No Selection", "Please select an annotation to delete.")

    def update_annotations(self):
        """Update annotations using AnnotationManager."""
        if not self.image_files:
            return
        
        current_image_name = self.image_files[self.current_image_index]
        self.annotation_manager.update_annotations_for_current_image(current_image_name)
        self.annotation_manager.save_annotations(self.images_folder) # Pass images_folder
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
        if current_image_name in self.annotation_manager.annotations and len(self.annotation_manager.annotations[current_image_name]) > 0:
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
                ann_count = len(self.annotation_manager.annotations[image_file]) # Use manager's annotations
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
    
    # Methods get_image_dimensions, load_existing_annotations, save_annotations are now in AnnotationManager
    # Calls will be self.annotation_manager.method_name(self.images_folder) or similar

    def preview_annotations(self):
        """Preview annotations from AnnotationManager's temp_annotations."""
        if not self.annotation_manager.temp_annotations: # Use manager's temp_annotations
            messagebox.showinfo("Preview", "No annotations to preview for current image.")
            return
        
        preview_text = f"Annotations for {self.image_files[self.current_image_index]}:\n\n"
        for i, ann in enumerate(self.annotation_manager.temp_annotations): # Use manager's temp_annotations
            status = "Visible" if ann.get('visible', True) else "Hidden"
            preview_text += f"{i+1}. Class: {ann['class']}\n"
            preview_text += f"   Bbox: {ann['bbox']}\n"
            preview_text += f"   Status: {status}\n"
            preview_text += f"   Color: {ann['color']}\n\n"
        
        messagebox.showinfo("Annotation Preview", preview_text)
    
    # Removed previous_image, next_image, train_model, try_model
    # Their logic is now in event_handlers.py and called from ui_components.py
    
    def complete_current_annotation(self):
        """Mark current image as completely annotated"""
        if not self.image_files:
            messagebox.showinfo("No Images", "Please load images first.")
            return
        
        current_image_name = self.image_files[self.current_image_index]
        
        # First make sure annotations are updated
        self.update_annotations()
        
        # Mark as annotated
        if current_image_name in self.annotation_manager.annotations and len(self.annotation_manager.annotations[current_image_name]) > 0: # Use manager
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
                
                # Annotation count for display in "Annotated" tab. Always show as completed.
                ann_count_for_display = len(self.annotation_manager.annotations.get(image_file, []))
                status_text = f"✅ {ann_count_for_display} annotations (Completed)"
                status_label = tk.Label(info_frame, text=status_text,
                                       bg=ModernColors.SIDEBAR_BG, 
                                       fg=ModernColors.BUTTON_SUCCESS, # Always success color for this tab
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
    
    # toggle_boxes_visibility and jump_to_image_by_number (the one that was bound to GUI)
    # were already removed or their logic moved to event_handlers.py.
    # The jump_to_image method below is for internal programmatic jumps.
    
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