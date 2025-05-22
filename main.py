import tkinter as tk
from app import AnnotationApp

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Configure root window
    root.tk.call('tk', 'scaling', 1.2)  # Improve DPI scaling
    
    # Initialize application
    app = AnnotationApp(root)
    
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
            app.cleanup()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Enhanced keyboard shortcuts
    root.bind('<Control-s>', lambda e: app.save_annotations())
    root.bind('<Control-n>', lambda e: app.next_image())
    root.bind('<Control-p>', lambda e: app.previous_image())
    root.bind('<Control-plus>', lambda e: app.canvas_area.on_mousewheel_zoom(type('obj', (object,), {'delta': 120})))
    root.bind('<Control-minus>', lambda e: app.canvas_area.on_mousewheel_zoom(type('obj', (object,), {'delta': -120})))
    root.bind('<Control-0>', lambda e: app.canvas_area.reset_zoom())
    root.bind('<space>', lambda e: app.toggle_boxes_visibility())
    root.bind('<Left>', lambda e: app.previous_image())
    root.bind('<Right>', lambda e: app.next_image())
    
    # Focus handling for proper keyboard shortcuts
    def on_focus_in(event):
        if hasattr(event.widget, 'winfo_class'):
            if event.widget.winfo_class() not in ['Entry', 'Text', 'Listbox']:
                root.focus_set()
    
    root.bind_all('<FocusIn>', on_focus_in)
    
    # Start application
    root.mainloop()

def run():
    """Alternative entry point"""
    main()

if __name__ == "__main__":
    main()
