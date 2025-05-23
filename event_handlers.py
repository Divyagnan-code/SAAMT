"""
Event handlers for the AI Annotation Tool.

This module contains functions that are triggered by UI events (e.g., button clicks,
mouse movements, selection changes) within the application. These handlers
typically receive the main application instance (`app`) to interact with its
state and methods.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os # Needed for select_folder_handler
# from PIL import Image # Not directly used in handlers after select_folder refactor
# import threading # Not directly used in handlers after select_folder refactor

# Note on select_folder_handler:
# The actual image loading (_load_images_async and its helpers) remains in AnnotationTool
# due to its complexity and tight coupling with the app's state (progress bar, etc.).
# A deeper refactoring would be needed for full separation.

# Import ModernColors for context menu styling, assuming direct import is preferred.
from ui_components import ModernColors # Used for styling context menu

def select_folder_handler(app: 'AnnotationTool'):
    """
    Handles the 'Select Images Folder' action.
    Opens a dialog for the user to select a folder and then initiates image loading.

    Args:
        app (AnnotationTool): The main application instance.
    """
    folder = filedialog.askdirectory(title="Select Images Folder")
    if folder:
        app.images_folder = folder
        app.load_images() # Calls the method on AnnotationTool instance

def previous_image_handler(app: 'AnnotationTool'):
    """
    Handles the 'Previous Image' action.
    Navigates to the previous image in the list if available.

    Args:
        app (AnnotationTool): The main application instance.
    """
    if app.image_files and app.current_image_index > 0:
        app.current_image_index -= 1
        app.load_current_image()

def next_image_handler(app: 'AnnotationTool'):
    """
    Handles the 'Next Image' action.
    Navigates to the next image in the list if available.

    Args:
        app (AnnotationTool): The main application instance.
    """
    if app.image_files and app.current_image_index < len(app.image_files) - 1:
        app.current_image_index += 1
        app.load_current_image()

def zoom_in_handler(app: 'AnnotationTool'):
    """
    Handles the 'Zoom In' action for the canvas.

    Args:
        app (AnnotationTool): The main application instance.
    """
    if app.zoom_factor < 5.0: # Max zoom limit
        app.zoom_factor *= 1.2
        app.display_image_on_canvas()

def zoom_out_handler(app: 'AnnotationTool'):
    """
    Handles the 'Zoom Out' action for the canvas.

    Args:
        app (AnnotationTool): The main application instance.
    """
    if app.zoom_factor > 0.1: # Min zoom limit
        app.zoom_factor /= 1.2
        app.display_image_on_canvas()

def reset_zoom_handler(app: 'AnnotationTool'):
    """
    Handles the 'Reset Zoom' action for the canvas.
    Resets zoom level to 1.0 and pan offsets to (0,0).

    Args:
        app (AnnotationTool): The main application instance.
    """
    app.zoom_factor = 1.0
    app.pan_x = 0
    app.pan_y = 0
    app.display_image_on_canvas()

def try_model_handler(app: 'AnnotationTool'):
    """
    Placeholder handler for the 'Try Model' action.
    Displays an informational message.

    Args:
        app (AnnotationTool): The main application instance.
    """
    messagebox.showinfo("Try Model", 
                        "🧪 Model testing functionality will be implemented in the next phase.\n\n"
                        "This will include:\n"
                        "• Load trained models\n"
                        "• Real-time inference\n"
                        "• Batch processing\n"
                        "• Results visualization")

def train_model_handler(app: 'AnnotationTool'):
    """
    Placeholder handler for the 'Train Model' action.
    Displays an informational message.

    Args:
        app (AnnotationTool): The main application instance.
    """
    messagebox.showinfo("Train Model", 
                        "🚀 Model training functionality will be implemented in the next phase.\n\n"
                        "This will include:\n"
                        "• Data preprocessing\n"
                        "• Model architecture selection\n"
                        "• Training progress monitoring\n"
                        "• Model evaluation metrics")

def on_mode_change_handler(app: 'AnnotationTool', event: Optional[tk.Event] = None):
    """
    Handles changes in the annotation mode selection (e.g., Combobox).
    Updates the available model list based on the new mode.

    Args:
        app (AnnotationTool): The main application instance.
        event (Optional[tk.Event]): The Tkinter event object (usually not directly used).
    """
    app.update_model_list() # Call the method on app instance to update models

def on_model_change_handler(app: 'AnnotationTool', event: Optional[tk.Event] = None):
    """
    Handles changes in the AI model selection (e.g., Combobox).
    Loads the selected model.

    Args:
        app (AnnotationTool): The main application instance.
        event (Optional[tk.Event]): The Tkinter event object (usually not directly used).
    """
    model_name = app.model_var.get() # model_var is a tk.StringVar on the app instance
    if model_name:
        mode = app.annotation_mode.get() # annotation_mode is a tk.StringVar on the app instance
        if app.model_manager.load_model(model_name, mode):
            app.update_status(f"Model '{model_name}' loaded successfully")
        else:
            app.update_status(f"Failed to load model '{model_name}'")

def on_confidence_change_handler(app: 'AnnotationTool', value: str):
    """
    Handles changes in the confidence threshold Scale widget.

    Args:
        app (AnnotationTool): The main application instance.
        value (str): The new value from the Scale widget (as a string).
    """
    app.model_manager.confidence_threshold = float(value)
    if hasattr(app, 'confidence_label'): # Ensure confidence_label widget exists on app
        app.confidence_label.configure(text=f"{float(value):.2f}")

def jump_to_image_by_number_handler(app: 'AnnotationTool', event: Optional[tk.Event] = None):
    """
    Handles jumping to an image by its number entered in an Entry widget.

    Args:
        app (AnnotationTool): The main application instance.
        event (Optional[tk.Event]): The Tkinter event object (e.g., if triggered by <Return> key).
    """
    if not app.image_files:
        messagebox.showinfo("No Images", "Please load images first.")
        return
    try:
        image_number_str = app.jump_var.get() # jump_var is a tk.StringVar on the app instance
        image_number = int(image_number_str)
        
        if 1 <= image_number <= len(app.image_files):
            app.current_image_index = image_number - 1
            app.load_current_image() # This method handles UI updates
            app.update_status(f"Navigated to image {image_number} of {len(app.image_files)}")
            if hasattr(app, 'jump_entry_widget'): # Optional: clear the entry widget
                 app.jump_entry_widget.delete(0, tk.END)
        else:
            messagebox.showwarning("Invalid Number", f"Please enter a number between 1 and {len(app.image_files)}")
    except ValueError:
        # Handles error if the input cannot be converted to an integer
        messagebox.showwarning("Invalid Input", "Please enter a valid number.")
    except AttributeError as e:
        # Handles error if jump_var or jump_entry_widget is not found on app (should not happen if UI is set up correctly)
        print(f"AttributeError in jump_to_image_by_number_handler: {e}")
        messagebox.showerror("Error", "Jump input UI element not found on app instance.")

def toggle_boxes_visibility_handler(app: 'AnnotationTool'):
    """
    Handles toggling the global visibility of all bounding boxes on the canvas.

    Args:
        app (AnnotationTool): The main application instance.
    """
    app.boxes_visible = not app.boxes_visible # Toggle the boolean flag
    app.display_image_on_canvas() # Refresh the canvas to show/hide boxes
    
    # Update the button text to reflect the new state
    status_text_display = "visible" if app.boxes_visible else "hidden"
    app.update_status(f"Bounding boxes {status_text_display}")
    if hasattr(app, 'visibility_btn'): # Ensure visibility_btn widget exists on app
        button_text = "👁️ Hide Boxes" if app.boxes_visible else "👁️ Show Boxes"
        app.visibility_btn.configure(text=button_text)


def toggle_selected_annotation_visibility_handler(app: 'AnnotationTool', index: int):
    """
    Toggles the visibility of a specific annotation in the temporary list.

    Args:
        app (AnnotationTool): The main application instance.
        index (int): The index of the annotation in `app.annotation_manager.temp_annotations`.
    """
    if app.annotation_manager.toggle_temp_annotation_visibility(index):
        app.save_state_for_undo() # Make action undoable
        app.display_image_on_canvas() # Refresh canvas to reflect change
        app.update_annotations_list() # Update listbox icons (👁️/🔒)
        
        # Provide feedback to the user via status bar
        ann_is_visible = app.annotation_manager.temp_annotations[index].get('visible', True)
        visibility_status_text = 'shown' if ann_is_visible else 'hidden'
        app.update_status(f"Annotation {index + 1} visibility toggled to {visibility_status_text}.")
    else:
        messagebox.showwarning("Visibility Error", "Invalid annotation index for visibility toggle.")

def show_annotation_list_context_menu_handler(app: 'AnnotationTool', event: tk.Event):
    """
    Shows a context menu for the annotations listbox upon a right-click event.

    Args:
        app (AnnotationTool): The main application instance.
        event (tk.Event): The Tkinter event object (contains x_root, y_root for menu popup).
    """
    try:
        # Determine the index of the item right-clicked
        # listbox.nearest(y) finds the line number nearest to y-coordinate
        index = app.annotations_listbox.nearest(event.y)
        
        # Check if the click was actually on an item or empty space in the listbox
        # .get(index) will raise an error if index is out of bounds (e.g., empty listbox)
        # or return empty string if the line exists but is empty (not typical for this app).
        # A more robust check is to see if index is within current item count.
        num_items = app.annotations_listbox.size()
        if index == -1 or index >= num_items : 
            app.annotations_listbox.selection_clear(0, tk.END) # Clear selection if click is on empty space
            return # Do not show context menu

        # Select the item under the cursor before showing the menu
        # This makes the context menu action apply to the right-clicked item
        app.annotations_listbox.selection_clear(0, tk.END)
        app.annotations_listbox.selection_set(index)
        app.annotations_listbox.activate(index) # Highlights the item
        
        # Ensure the index is valid for the actual data source (temp_annotations)
        if 0 <= index < len(app.annotation_manager.temp_annotations):
            # Create the context menu
            context_menu = tk.Menu(app.annotations_listbox, tearoff=0, 
                                   bg=ModernColors.SIDEBAR_BG, # Use directly imported ModernColors
                                   fg=ModernColors.TEXT_PRIMARY)
            
            # Determine current visibility to set menu item text correctly
            annotation_is_visible = app.annotation_manager.temp_annotations[index].get('visible', True)
            visibility_action_text = "Hide" if annotation_is_visible else "Show"
            
            context_menu.add_command(label=f"{visibility_action_text} Annotation", 
                                     command=lambda: toggle_selected_annotation_visibility_handler(app, index))
            
            # --- Example of adding more actions to the context menu ---
            # context_menu.add_separator()
            # context_menu.add_command(label="Change Color", 
            #                          command=lambda: app.change_annotation_color_by_index(index)) # Assumes app has this method
            # context_menu.add_command(label="Delete", 
            #                          command=lambda: app.delete_annotation_by_index(index)) # Assumes app has this method
            
            # Display the menu at the cursor's position
            context_menu.tk_popup(event.x_root, event.y_root)
    except Exception as e:
        # Catch any unexpected errors during context menu creation or display
        print(f"Error in show_annotation_list_context_menu_handler: {e}")
        messagebox.showerror("Menu Error", "Could not display context menu.")

# Type hinting for 'app' argument when AnnotationTool is in a different module and causes circular import
# This is a common way to handle type hints for classes defined elsewhere or to avoid circular dependencies.
# However, since event_handlers are typically called from ui_new.py where AnnotationTool is defined,
# direct type hinting like `app: 'AnnotationTool'` (using forward reference string) is fine within ui_new.py.
# If these handlers were in a module that AnnotationTool imports, then 'AnnotationTool' as a string hint is necessary.
# For this project structure, 'AnnotationTool' might not be directly known here without such a forward reference
# if we were to strictly type check this file standalone.
# The `app: 'AnnotationTool'` in function signatures is a forward reference.
# Python's type checker (like Mypy) can understand this if it processes all files.
# No actual import of AnnotationTool is needed here, which is good for modularity.
