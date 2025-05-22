import os
import json
import copy
from typing import Dict, List, Tuple, Optional

class AnnotationManager:
    """Manages annotation data and operations"""
    def __init__(self):
        self.annotations = {}  # filename -> list of annotation objects
        self.annotated_images = set()  # Set of images marked as fully annotated
        self.temp_annotations = []  # Temporary annotations (during drawing)
        self.last_copied_annotation = None  # For copy-paste functionality
        self.current_class = "person"  # Default class
        self.annotation_colors = ['#ff4444', '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff']
        self.color_index = 0
    
    def add_annotation(self, image_name, annotation):
        """Add an annotation to the specified image"""
        if image_name not in self.annotations:
            self.annotations[image_name] = []
        
        # Add a unique ID to the annotation
        if 'id' not in annotation:
            annotation['id'] = self._generate_annotation_id(image_name)
        
        self.annotations[image_name].append(annotation)
        return annotation['id']
    
    def update_annotation(self, image_name, annotation_id, updated_annotation):
        """Update an existing annotation"""
        if image_name not in self.annotations:
            return False
        
        for i, ann in enumerate(self.annotations[image_name]):
            if ann.get('id') == annotation_id:
                self.annotations[image_name][i] = updated_annotation
                return True
        
        return False
    
    def delete_annotation(self, image_name, annotation_id):
        """Delete an annotation by its ID"""
        if image_name not in self.annotations:
            return False
        
        for i, ann in enumerate(self.annotations[image_name]):
            if ann.get('id') == annotation_id:
                del self.annotations[image_name][i]
                return True
        
        return False
    
    def get_annotations(self, image_name):
        """Get all annotations for an image"""
        return self.annotations.get(image_name, [])
    
    def mark_as_annotated(self, image_name):
        """Mark an image as completely annotated"""
        if image_name in self.annotations and len(self.annotations[image_name]) > 0:
            self.annotated_images.add(image_name)
            return True
        return False
    
    def is_annotated(self, image_name):
        """Check if an image is marked as annotated"""
        return image_name in self.annotated_images
    
    def get_annotated_images(self):
        """Get list of annotated image names"""
        return list(self.annotated_images)
    
    def save_annotations(self, folder_path):
        """Save annotations to JSON files"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        for image_name, image_annotations in self.annotations.items():
            if not image_annotations:  # Skip empty annotations
                continue
            
            # Create filename from image name
            json_filename = os.path.splitext(image_name)[0] + '.json'
            json_path = os.path.join(folder_path, json_filename)
            
            try:
                with open(json_path, 'w') as f:
                    # Include annotation status
                    data = {
                        'annotations': image_annotations,
                        'is_fully_annotated': image_name in self.annotated_images
                    }
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving annotations for {image_name}: {e}")
    
    def load_annotations(self, folder_path, image_files):
        """Load annotations from JSON files"""
        self.annotations = {}
        self.annotated_images = set()
        
        for image_name in image_files:
            json_filename = os.path.splitext(image_name)[0] + '.json'
            json_path = os.path.join(folder_path, json_filename)
            
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        
                        # Handle both new format (with is_fully_annotated) and old format
                        if isinstance(data, dict) and 'annotations' in data:
                            self.annotations[image_name] = data['annotations']
                            if data.get('is_fully_annotated', False):
                                self.annotated_images.add(image_name)
                        else:  # Old format (just a list of annotations)
                            self.annotations[image_name] = data
                except Exception as e:
                    print(f"Error loading annotations for {image_name}: {e}")
    
    def copy_annotation(self, image_name, annotation_id):
        """Copy an annotation for later pasting"""
        if image_name not in self.annotations:
            return False
        
        for ann in self.annotations[image_name]:
            if ann.get('id') == annotation_id:
                self.last_copied_annotation = copy.deepcopy(ann)
                return True
        
        return False
    
    def paste_annotation(self, image_name, position_offset=(0, 0)):
        """Paste the previously copied annotation"""
        if not self.last_copied_annotation:
            return False
        
        # Create a new annotation based on the copied one
        new_annotation = copy.deepcopy(self.last_copied_annotation)
        
        # Modify the bbox with the offset
        if 'bbox' in new_annotation:
            x1, y1, x2, y2 = new_annotation['bbox']
            offset_x, offset_y = position_offset
            new_annotation['bbox'] = [x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y]
        
        # Generate a new ID
        new_annotation['id'] = self._generate_annotation_id(image_name)
        
        # Add to annotations
        self.add_annotation(image_name, new_annotation)
        return True
    
    def _generate_annotation_id(self, image_name):
        """Generate a unique ID for a new annotation"""
        existing_ids = set()
        if image_name in self.annotations:
            for ann in self.annotations[image_name]:
                if 'id' in ann:
                    existing_ids.add(ann['id'])
        
        # Find the next available ID
        next_id = 1
        while next_id in existing_ids:
            next_id += 1
        
        return next_id
    
    def get_next_color(self):
        """Get the next color in the rotation for a new annotation"""
        color = self.annotation_colors[self.color_index]
        self.color_index = (self.color_index + 1) % len(self.annotation_colors)
        return color
