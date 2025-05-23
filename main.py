"""
Main entry point for the enhanced AI annotation tool.
"""

import tkinter as tk
import os
import sys

# Add the current directory to the path so modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import UI modules
from modules.ui_integrated import AnnotationToolIntegrated

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Configure root window
    root.tk.call('tk', 'scaling', 1.2)  # Improve DPI scaling
    
    # Initialize application
    app = AnnotationToolIntegrated(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Handle window closing
    def on_closing():
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?\n\nAny unsaved annotations will be lost."):
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

if __name__ == "__main__":
    main()
