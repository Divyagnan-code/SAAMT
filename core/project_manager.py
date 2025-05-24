# core/project_manager.py
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Project:
    """Project data structure"""
    name: str
    path: str
    description: str
    created_at: str
    modified_at: str
    image_directory: str
    annotation_format: str
    classes: Dict[int, str]
    settings: Dict
    
    def to_dict(self):
        return asdict(self)

class ProjectManager:
    """Manages annotation projects"""
    
    def __init__(self, projects_dir: str):
        self.projects_dir = Path(projects_dir)
        self.current_project: Optional[Project] = None
        self.projects: Dict[str, Project] = {}
        
        logger.info(f"ProjectManager initialized with directory: {projects_dir}")
        self._create_projects_directory()
        self._load_existing_projects()
    
    def _create_projects_directory(self):
        """Create projects directory if it doesn't exist"""
        try:
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Projects directory ensured: {self.projects_dir}")
        except Exception as e:
            logger.error(f"Failed to create projects directory: {e}")
            raise
    
    def _load_existing_projects(self):
        """Load existing projects from disk"""
        logger.debug("Loading existing projects")
        
        try:
            for project_dir in self.projects_dir.iterdir():
                if project_dir.is_dir():
                    project_file = project_dir / "project.json"
                    if project_file.exists():
                        try:
                            project = self._load_project_file(project_file)
                            self.projects[project.name] = project
                            logger.debug(f"Loaded project: {project.name}")
                        except Exception as e:
                            logger.error(f"Failed to load project from {project_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load existing projects: {e}")
    
    def create_project(self, name: str, description: str, image_directory: str, 
                      annotation_format: str = "JSON") -> Project:
        """Create a new project"""
        logger.info(f"Creating new project: {name}")
        
        if name in self.projects:
            raise ValueError(f"Project '{name}' already exists")
        
        # Create project directory
        project_path = self.projects_dir / name
        project_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (project_path / "annotations").mkdir(exist_ok=True)
        (project_path / "exports").mkdir(exist_ok=True)
        (project_path / "backups").mkdir(exist_ok=True)
        
        # Create project object
        project = Project(
            name=name,
            path=str(project_path),
            description=description,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
            image_directory=image_directory,
            annotation_format=annotation_format,
            classes={},
            settings={}
        )
        
        # Save project
        self._save_project(project)
        self.projects[name] = project
        
        logger.info(f"Project '{name}' created successfully")
        return project
    
    def load_project(self, name: str) -> Project:
        """Load a project"""
        logger.info(f"Loading project: {name}")
        
        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found")
        
        self.current_project = self.projects[name]
        logger.info(f"Project '{name}' loaded successfully")
        return self.current_project
    
    def get_current_project(self) -> Optional[Project]:
        """Get current project"""
        return self.current_project
    
    def list_projects(self) -> List[str]:
        """List all available projects"""
        return list(self.projects.keys())
    
    def delete_project(self, name: str):
        """Delete a project"""
        logger.info(f"Deleting project: {name}")
        
        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found")
        
        project = self.projects[name]
        
        # Remove project directory
        import shutil
        shutil.rmtree(project.path)
        
        # Remove from memory
        del self.projects[name]
        
        if self.current_project and self.current_project.name == name:
            self.current_project = None
        
        logger.info(f"Project '{name}' deleted successfully")
    
    def update_project(self, name: str, **kwargs):
        """Update project settings"""
        logger.debug(f"Updating project: {name}")
        
        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found")
        
        project = self.projects[name]
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.modified_at = datetime.now().isoformat()
        self._save_project(project)
        
        logger.debug(f"Project '{name}' updated successfully")
    
    def _save_project(self, project: Project):
        """Save project to disk"""
        project_file = Path(project.path) / "project.json"
        
        try:
            with open(project_file, 'w') as f:
                json.dump(project.to_dict(), f, indent=2)
            logger.debug(f"Project saved: {project_file}")
        except Exception as e:
            logger.error(f"Failed to save project {project.name}: {e}")
            raise
    
    def _load_project_file(self, project_file: Path) -> Project:
        """Load project from file"""
        with open(project_file, 'r') as f:
            data = json.load(f)
        
        return Project(**data)