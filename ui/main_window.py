import sys
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
                           QMessageBox, QFileDialog, QProgressBar, QLabel)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence
from typing import List
from .annotation_widget import AnnotationWidget
from .image_list_widget import ImageListWidget
from .tools_panel import ToolsPanel
from .dialogs import ProjectDialog, SettingsDialog, AboutDialog
from core.annotation_manager import AnnotationManager
from core.project_manager import ProjectManager
from core.image_processor import ImageProcessor
from model.inference_engine import InferenceEngine
from config.settings import SETTINGS, save_user_settings

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    project_changed = pyqtSignal(str)
    image_selected = pyqtSignal(str)
    annotation_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow")
        
        # Initialize core components
        self.annotation_manager = AnnotationManager()
        self.project_manager = ProjectManager(SETTINGS['PATHS']['projects_dir'])
        self.image_processor = ImageProcessor()
        self.inference_engine = InferenceEngine(SETTINGS['PATHS']['models_dir'])
        
        # UI components
        self.annotation_widget = None
        self.image_list_widget = None
        self.tools_panel = None
        
        # Status tracking
        self.current_project = None
        self.current_image = None
        self.auto_save_timer = QTimer()
        
        self._setup_ui()
        self._setup_connections()
        self._setup_auto_save()
        
        logger.info("MainWindow initialized successfully")
    
    def _setup_ui(self):
        """Setup the user interface"""
        logger.debug("Setting up UI")
        
        # Set window properties
        self.setWindowTitle("Advanced Image Annotation Framework")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
        
        # Create main layout
        self._create_main_layout()
        
        # Set initial state
        self._update_ui_state()
    
    def _create_menu_bar(self):
        """Create menu bar"""
        logger.debug("Creating menu bar")
        
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # New project
        new_project_action = QAction('&New Project...', self)
        new_project_action.setShortcut(QKeySequence.New)
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)
        
        # Open project
        open_project_action = QAction('&Open Project...', self)
        open_project_action.setShortcut(QKeySequence.Open)
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        # Save annotations
        save_action = QAction('&Save Annotations', self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_annotations)
        file_menu.addAction(save_action)
        
        # Export annotations
        export_action = QAction('&Export Annotations...', self)
        export_action.triggered.connect(self._export_annotations)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('&Edit')
        
        # Undo Ректорен
        undo_action = QAction('&Undo', self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        # Redo
        redo_action = QAction('&Redo', self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Settings
        settings_action = QAction('&Settings...', self)
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Toggle panels
        toggle_tools_action = QAction('Toggle &Tools Panel', self)
        toggle_tools_action.setCheckable(True)
        toggle_tools_action.setChecked(True)
        toggle_tools_action.triggered.connect(self._toggle_tools_panel)
        view_menu.addAction(toggle_tools_action)
        
        toggle_images_action = QAction('Toggle &Images Panel', self)
        toggle_images_action.setCheckable(True)
        toggle_images_action.setChecked(True)
        toggle_images_action.triggered.connect(self._toggle_images_panel)
        view_menu.addAction(toggle_images_action)
        
        # Models menu
        models_menu = menubar.addMenu('&Models')
        
        # Load model
        load_model_action = QAction('&Load Model...', self)
        load_model_action.triggered.connect(self._load_model)
        models_menu.addAction(load_model_action)
        
        # Auto-annotate
        auto_annotate_action = QAction('&Auto-Annotate Current Image', self)
        auto_annotate_action.triggered.connect(self._auto_annotate_current)
        models_menu.addAction(auto_annotate_action)
        
        # Batch auto-annotate
        batch_annotate_action = QAction('&Batch Auto-Annotate...', self)
        batch_annotate_action.triggered.connect(self._batch_auto_annotate)
        models_menu.addAction(batch_annotate_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About
        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create status bar"""
        logger.debug("Creating status bar")
        
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.status_bar.addPermanentWidget(self.project_label)
    
    def _create_main_layout(self):
        """Create main layout"""
        logger.debug("Creating main layout")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel (image list + tools)
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setFixedWidth(300)
        
        # Image list widget
        self.image_list_widget = ImageListWidget()
        left_splitter.addWidget(self.image_list_widget)
        
        # Tools panel
        self.tools_panel = ToolsPanel()
        left_splitter.addWidget(self.tools_panel)
        
        # Set left splitter sizes
        left_splitter.setSizes([400, 300])
        
        # Add left panel to main splitter
        main_splitter.addWidget(left_splitter)
        
        # Annotation widget (center)
        self.annotation_widget = AnnotationWidget()
        main_splitter.addWidget(self.annotation_widget)
        
        # Set main splitter sizes
        main_splitter.setSizes([300, 1100])
        
        # Main layout
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)
    
    def _setup_connections(self):
        """Setup signal connections"""
        logger.debug("Setting up connections")
        
        # Image list connections
        self.image_list_widget.image_selected.connect(self._on_image_selected)
        self.image_list_widget.images_loaded.connect(self._on_images_loaded)
        
        # Tools panel connections
        self.tools_panel.tool_changed.connect(self._on_tool_changed)
        self.tools_panel.class_changed.connect(self._on_class_changed)
        self.tools_panel.threshold_changed.connect(self._on_threshold_changed)
        self.tools_panel.auto_annotate_requested.connect(self._auto_annotate_current)
        
        # Annotation widget connections
        self.annotation_widget.annotation_added.connect(self._on_annotation_added)
        self.annotation_widget.annotation_removed.connect(self._on_annotation_removed)
        self.annotation_widget.annotation_modified.connect(self._on_annotation_modified)
        
        # Internal connections
        self.project_changed.connect(self._on_project_changed)
        self.image_selected.connect(self._on_image_changed)
        self.annotation_updated.connect(self._on_annotation_updated)
    
    def _setup_auto_save(self):
        """Setup auto-save functionality"""
        logger.debug("Setting up auto-save")
        
        if SETTINGS['UI']['auto_save']:
            self.auto_save_timer.timeout.connect(self._auto_save)
            self.auto_save_timer.start(SETTINGS['UI']['auto_save_interval'] * 1000)
    
    def _update_ui_state(self):
        """Update UI state based on current project and image"""
        logger.debug("Updating UI state")
        
        has_project = self.current_project is not None
        has_image = self.current_image is not None
        
        # Update status
        if has_project:
            project_name = self.current_project.name
            stats = self.annotation_manager.get_annotation_stats()
            status_text = f"Project: {project_name} | Images: {stats['total_images']} | Annotated: {stats['annotated_images']}"
            self.project_label.setText(status_text)
        else:
            self.project_label.setText("No project loaded")
        
        # Update tools panel
        self.tools_panel.setEnabled(has_project)
        
        # Update annotation widget
        self.annotation_widget.setEnabled(has_image)
    
    # Slot implementations
    def _new_project(self):
        """Create new project"""
        logger.info("Creating new project")
        
        dialog = ProjectDialog(self)
        if dialog.exec_() == dialog.Accepted:
            try:
                project_data = dialog.get_project_data()
                project = self.project_manager.create_project(**project_data)
                
                self.current_project = project
                self.project_changed.emit(project.name)
                self.image_list_widget.load_images(project_data['image_directory'])
                
                self.status_label.setText(f"Project '{project.name}' created successfully")
                
            except Exception as e:
                logger.error(f"Failed to create project: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to create project:\n{str(e)}")
    
    def _open_project(self):
        """Open existing project"""
        logger.info("Opening project")
        
        projects = self.project_manager.list_projects()
        if not projects:
            QMessageBox.information(self, "No Projects", "No projects found. Create a new project first.")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        project_name, ok = QInputDialog.getItem(self, "Open Project", "Select project:", projects, 0, False)
        
        if ok and project_name:
            try:
                project = self.project_manager.load_project(project_name)
                self.current_project = project
                self.project_changed.emit(project.name)
                self.image_list_widget.load_images(project.image_directory)
                
                self.status_label.setText(f"Project '{project.name}' loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load project: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")
    
    def _save_annotations(self):
        """Save current annotations to the project"""
        logger.info("Saving annotations")
        
        if not self.current_project:
            logger.warning("No project loaded, cannot save annotations")
            QMessageBox.warning(self, "Warning", "No project is loaded. Please create or open a project first.")
            return
        
        try:
            self.annotation_manager.save_annotations(self.current_project)
            self.status_label.setText("Annotations saved successfully")
            logger.info("Annotations saved successfully")
        except Exception as e:
            logger.error(f"Failed to save annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save annotations:\n{str(e)}")
    
    def _export_annotations(self):
        """Export annotations to a file"""
        logger.info("Exporting annotations")
        
        if not self.current_project:
            logger.warning("No project loaded, cannot export annotations")
            QMessageBox.warning(self, "Warning", "No project is loaded. Please create or open a project first.")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Export Annotations", "", "JSON Files (*.json);;All Files (*)")
            if file_path:
                self.annotation_manager.export_annotations(self.current_project, file_path)
                self.status_label.setText(f"Annotations exported to {file_path}")
                logger.info(f"Annotations exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export annotations: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export annotations:\n{str(e)}")
    
    def _undo(self):
        """Undo the last annotation action"""
        logger.info("Undoing last annotation action")
        
        if not self.current_project or not self.current_image:
            logger.warning("No project or image loaded, cannot undo")
            QMessageBox.warning(self, "Warning", "No project or image is loaded. Please load a project and select an image.")
            return
        
        try:
            self.annotation_manager.undo(self.current_project, self.current_image)
            self.annotation_updated.emit()
            self.status_label.setText("Undo successful")
            logger.info("Undo successful")
        except Exception as e:
            logger.error(f"Failed to undo: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to undo:\n{str(e)}")
    
    def _redo(self):
        """Redo the last undone annotation action"""
        logger.info("Redoing last undone annotation action")
        
        if not self.current_project or not self.current_image:
            logger.warning("No project or image loaded, cannot redo")
            QMessageBox.warning(self, "Warning", "No project or image is loaded. Please load a project and select an image.")
            return
        
        try:
            self.annotation_manager.redo(self.current_project, self.current_image)
            self.annotation_updated.emit()
            self.status_label.setText("Redo successful")
            logger.info("Redo successful")
        except Exception as e:
            logger.error(f"Failed to redo: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to redo:\n{str(e)}")
    
    def _show_settings(self):
        """Show settings dialog"""
        logger.info("Opening settings dialog")
        
        dialog = SettingsDialog(self)
        if dialog.exec_() == dialog.Accepted:
            try:
                new_settings = dialog.get_settings()
                save_user_settings(new_settings)
                SETTINGS.update(new_settings)  # Update global SETTINGS
                self._setup_auto_save()  # Reconfigure auto-save with new settings
                self.status_label.setText("Settings saved successfully")
                logger.info("Settings saved successfully")
            except Exception as e:
                logger.error(f"Failed to save settings: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
    
    def _toggle_tools_panel(self):
        """Toggle visibility of the tools panel"""
        logger.info("Toggling tools panel visibility")
        
        self.tools_panel.setVisible(not self.tools_panel.isVisible())
        self.status_label.setText("Tools panel toggled" if self.tools_panel.isVisible() else "Tools panel hidden")
        logger.info(f"Tools panel {'visible' if self.tools_panel.isVisible() else 'hidden'}")
    
    def _toggle_images_panel(self):
        """Toggle visibility of the images panel"""
        logger.info("Toggle images panel visibility")
        
        self.image_list_widget.setVisible(not self.image_list_widget.isVisible())
        self.status_label.setText("Images panel toggled" if self.image_list_widget.isVisible() else "Images panel hidden")
        logger.info(f"Images panel {'visible' if self.image_list_widget.isVisible() else 'hidden'}")
    
    def _load_model(self):
        """Load a machine learning model for auto-annotation"""
        logger.info("Loading model")
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Model", SETTINGS['PATHS']['models_dir'], "Model Files (*.pth *.onnx);;All Files (*)")
            if file_path:
                self.inference_engine.load_model(file_path)
                self.tools_panel.update_models({os.path.basename(file_path): file_path})
                self.status_label.setText(f"Model loaded from {file_path}")
                logger.info(f"Model loaded from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load model:\n{str(e)}")
    
    def _auto_annotate_current(self):
        """Auto-annotate the current image using the loaded model"""
        logger.info("Auto-annotating current image")
        
        if not self.current_project or not self.current_image:
            logger.warning("No project or image loaded, cannot auto-annotate")
            QMessageBox.warning(self, "Warning", "No project or image is loaded. Please load a project and select an image.")
            return
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            annotations = self.inference_engine.infer(self.current_image)
            self.annotation_manager.add_annotations(self.current_project, self.current_image, annotations)
            self.annotation_updated.emit()
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            self.status_label.setText("Auto-annotation completed")
            logger.info("Auto-annotation completed")
        except Exception as e:
            logger.error(f"Failed to auto-annotate: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to auto-annotate:\n{str(e)}")
            self.progress_bar.setVisible(False)
    
    def _batch_auto_annotate(self):
        """Batch auto-annotate all images in the project"""
        logger.info("Starting batch auto-annotation")
        
        if not self.current_project:
            logger.warning("No project loaded, cannot batch auto-annotate")
            QMessageBox.warning(self, "Warning", "No project is loaded. Please create or open a project first.")
            return
        
        try:
            images = self.project_manager.get_images(self.current_project)
            total = len(images)
            if not total:
                QMessageBox.information(self, "No Images", "No images found in the project.")
                return
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, total)
            
            for i, image_path in enumerate(images):
                annotations = self.inference_engine.infer(image_path)
                self.annotation_manager.add_annotations(self.current_project, image_path, annotations)
                self.progress_bar.setValue(i + 1)
            
            self.annotation_updated.emit()
            self.progress_bar.setVisible(False)
            self.status_label.setText("Batch auto-annotation completed")
            logger.info("Batch auto-annotation completed")
        except Exception as e:
            logger.error(f"Failed to batch auto-annotate: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to batch auto-annotate:\n{str(e)}")
            self.progress_bar.setVisible(False)
    
    def _show_about(self):
        """Show about dialog"""
        logger.info("Opening about dialog")
        
        dialog = AboutDialog(self)
        dialog.exec_()
        logger.info("About dialog closed")
    
    def _auto_save(self):
        """Auto-save annotations if modified"""
        logger.debug("Performing auto-save")
        
        if self.current_project:
            try:
                self.annotation_manager.save_annotations(self.current_project)
                logger.debug("Auto-save completed")
            except Exception as e:
                logger.error(f"Auto-save failed: {str(e)}")
    
    def _on_image_selected(self, image_path: str):
        """Handle image selection"""
        logger.debug(f"Image selected: {image_path}")
        self.current_image = image_path
        self.annotation_widget.set_image(image_path)
        self.image_selected.emit(image_path)
    
    def _on_images_loaded(self):
        """Handle images loaded"""
        logger.debug("Images loaded")
        self._update_ui_state()
    
    def _on_tool_changed(self, tool: str):
        """Handle tool change"""
        logger.debug(f"Tool changed: {tool}")
        self.annotation_widget.set_tool(tool)
    
    def _on_class_changed(self, class_id: int, class_name: str):
        """Handle class change"""
        logger.debug(f"Class changed: {class_id} - {class_name}")
        self.annotation_widget.set_class(class_id, class_name)
    
    def _on_threshold_changed(self, threshold: float):
        """Handle threshold change"""
        logger.debug(f"Threshold changed: {threshold}")
        # Update threshold in inference engine if needed
        self.inference_engine.set_confidence_threshold(threshold)
    
    def _on_annotation_added(self, annotation: dict):
        """Handle annotation added"""
        logger.debug(f"Annotation added: {annotation}")
        self._update_ui_state()
        self.annotation_updated.emit()
    
    def _on_annotation_removed(self, annotation_id: int):
        """Handle annotation removed"""
        logger.debug(f"Annotation removed: {annotation_id}")
        self._update_ui_state()
        self.annotation_updated.emit()
    
    def _on_annotation_modified(self):
        """Handle annotation modified"""
        logger.debug("Annotation modified")
        self._update_ui_state()
        self.annotation_updated.emit()
    
    def _on_project_changed(self, project_name: str):
        """Handle project change"""
        logger.debug(f"Project changed: {project_name}")
        self._update_ui_state()
    
    def _on_image_changed(self, image_path: str):
        """Handle image change"""
        logger.debug(f"Image changed: {image_path}")
        self._update_ui_state()
    
    def _on_annotation_updated(self):
        """Handle annotation update"""
        logger.debug("Annotation updated")
        self._update_ui_state()