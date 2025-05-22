<<<<<<< HEAD
# SAAMT
A framework for annotating and training models
=======
# Enhanced AI Annotation Tool

A powerful image annotation tool with AI assistance capabilities, built with Python and Tkinter.

## Features

- Load and navigate through image collections
- Create, edit, and manage bounding box annotations
- Toggle annotation visibility
- Complete annotation tracking
- AI model integration for automatic object detection
- Undo/redo functionality
- Copy/paste annotations
- Zoom and pan support
- Keyboard shortcuts for efficient workflow

## Project Structure

The project has been refactored into a modular structure:

```
annotator/
├── main.py             # Application entry point
├── app.py              # Main application controller
├── ui/                 # User interface modules
│   ├── __init__.py
│   ├── styles.py       # UI styles and theme definitions
│   ├── sidebar.py      # Sidebar with thumbnails and navigation
│   ├── toolbar.py      # Top toolbar with main controls
│   ├── canvas.py       # Main annotation canvas area
│   └── controls.py     # Right-side annotation controls panel
├── core/               # Core functionality modules
│   ├── __init__.py
│   ├── image_manager.py     # Image loading and navigation
│   ├── annotation_manager.py # Annotation data handling
│   ├── model_manager.py     # AI model integration
│   └── undo_manager.py      # Undo/redo functionality
└── utils/              # Utility modules
    └── __init__.py
```

## Module Descriptions

### UI Modules

- **styles.py**: Contains the color theme (ModernColors) and custom UI elements (ModernButton)
- **sidebar.py**: Implements the left sidebar with thumbnail navigation and tabs for all/annotated images
- **toolbar.py**: Implements the top toolbar with file operations, model controls, and drawing tools
- **canvas.py**: Implements the main canvas area for displaying images and handling annotations
- **controls.py**: Implements the right sidebar with annotation details and statistics

### Core Modules

- **image_manager.py**: Handles image loading, navigation, and thumbnail generation
- **annotation_manager.py**: Manages annotation data, including saving/loading from disk
- **model_manager.py**: Integrates with AI models for automated object detection
- **undo_manager.py**: Provides undo/redo functionality for annotation operations

## Running the Application

To run the application, execute:

```bash
python main.py
```

## Keyboard Shortcuts

- **Ctrl+S**: Save annotations
- **Ctrl+Z**: Undo
- **Ctrl+Y** or **Ctrl+Shift+Z**: Redo
- **Ctrl+C**: Copy selected annotation
- **Ctrl+V**: Paste annotation
- **Delete** or **Backspace**: Delete selected annotation
- **Space**: Toggle box visibility
- **Ctrl+0**: Reset zoom
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Left/Right Arrow**: Previous/Next image

## Extending the Application

The modular design makes it easy to extend the application:

- Add new AI models by extending the ModelManager class
- Implement new annotation types by modifying the AnnotationManager and canvas display code
- Add new UI features by creating new UI component modules
>>>>>>> 446b6c3 (modular approach)
