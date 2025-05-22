import tkinter as tk

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
