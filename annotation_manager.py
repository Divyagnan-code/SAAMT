"""
Manages all aspects of annotation data for the AI Annotation Tool.

This module includes the AnnotationManager class, which is responsible for
storing, loading, saving, and manipulating annotations both for the entire
dataset (persistent storage) and for the currently active image (temporary,
in-memory annotations). It handles operations like creating, deleting,
copying, pasting, and changing properties (color, class) of annotations.
"""
import os
import json # Not currently used, but could be for different save formats
import copy
from typing import Dict, List, Tuple, Optional, Any # Added Any for annotation dict values
from PIL import Image

class AnnotationManager:
    """
    Handles the lifecycle and manipulation of annotation data.

    This includes loading annotations from a file, saving them, managing
    temporary annotations for the currently displayed image, and providing
    methods for common annotation operations.
    """
    def __init__(self):
        """
        Initializes the AnnotationManager with empty annotation stores and default settings.
        """
        # Stores all annotations for all images, typically loaded from/saved to a file.
        # Key: image filename (str), Value: List of annotation dictionaries.
        self.annotations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Stores annotations for the currently active image being edited.
        self.temp_annotations: List[Dict[str, Any]] = []
        
        # Stores the last annotation that was copied, for paste operations.
        self.last_copied_annotation: Optional[Dict[str, Any]] = None
        
        # Default class for new annotations.
        self.current_class: str = "person"
        
        # Predefined list of colors for new annotations.
        self.annotation_colors: List[str] = ['#ff4444', '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff']
        
        # Index to cycle through annotation_colors.
        self.color_index: int = 0

    def get_image_dimensions(self, image_name: str, images_folder: str) -> Tuple[int, int]:
        """
        Retrieves the width and height of a given image.

        Args:
            image_name (str): The filename of the image.
            images_folder (str): The path to the folder containing the image.

        Returns:
            Tuple[int, int]: A tuple (width, height) of the image.
                             Returns (640, 480) as a fallback if the image cannot be opened.
        """
        try:
            image_path = os.path.join(images_folder, image_name)
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error getting dimensions for image '{image_name}': {e}")
            return 640, 480 # Default or fallback size

    def load_existing_annotations(self, images_folder: str):
        """
        Loads annotations from a 'annotations.txt' file within the specified images folder.

        The expected format is one annotation per line:
        image_name,class_name,center_x_norm,center_y_norm,width_norm,height_norm

        Args:
            images_folder (str): The path to the folder where 'annotations.txt' is located.
        """
        if not images_folder:
            print("Error: Image folder not specified. Cannot load annotations.")
            return
        
        annotations_file = os.path.join(images_folder, "annotations.txt")
        if os.path.exists(annotations_file):
            try:
                self.annotations = {} # Clear existing annotations before loading
                with open(annotations_file, 'r') as f:
                    for line_number, line in enumerate(f, 1):
                        parts = line.strip().split(',')
                        if len(parts) >= 6:
                            image_name: str = parts[0]
                            class_name: str = parts[1]
                            
                            # Perform robust conversion for numeric parts
                            try:
                                center_x: float = float(parts[2])
                                center_y: float = float(parts[3])
                                width: float = float(parts[4])
                                height: float = float(parts[5])
                            except ValueError as ve:
                                print(f"Warning: Skipping line {line_number} in {annotations_file} due to invalid numeric value: {ve}")
                                continue

                            img_width, img_height = self.get_image_dimensions(image_name, images_folder)
                            if img_width == 0 or img_height == 0:
                                print(f"Warning: Skipping annotation for image '{image_name}' (line {line_number}) due to zero image dimensions.")
                                continue
                            
                            # Convert normalized YOLO-like coordinates to absolute pixel coordinates [x1, y1, x2, y2]
                            x1: int = int((center_x - width / 2) * img_width)
                            y1: int = int((center_y - height / 2) * img_height)
                            x2: int = int((center_x + width / 2) * img_width)
                            y2: int = int((center_y + height / 2) * img_height)
                            
                            # Assign a color based on the current number of annotations for this image or globally
                            color: str = self.annotation_colors[len(self.annotations.get(image_name, [])) % len(self.annotation_colors)]
                            
                            annotation: Dict[str, Any] = {
                                'class': class_name,
                                'bbox': [x1, y1, x2, y2],
                                'visible': True, # Annotations loaded from file are visible by default
                                'color': color
                            }
                            
                            if image_name not in self.annotations:
                                self.annotations[image_name] = []
                            self.annotations[image_name].append(annotation)
                        else:
                            print(f"Warning: Skipping malformed line {line_number} in {annotations_file}: {line.strip()}")
            except Exception as e:
                # Catch any other unexpected errors during the loading process
                print(f"Error loading annotations from '{annotations_file}': {e}")
        else:
            # This is not an error, just a common case for new projects
            print(f"Annotations file not found: '{annotations_file}'. Starting with no pre-loaded annotations.")

    def save_annotations(self, images_folder: str):
        """
        Saves all annotations to 'annotations.txt' in the specified images folder.

        Annotations are saved in a YOLO-like format:
        image_name,class_name,center_x_norm,center_y_norm,width_norm,height_norm

        Args:
            images_folder (str): The path to the folder where 'annotations.txt' will be saved.
        """
        if not images_folder:
            print("Error: Image folder not specified. Cannot save annotations.")
            return
        
        annotations_file = os.path.join(images_folder, "annotations.txt")
        try:
            with open(annotations_file, 'w') as f:
                for image_name, anns in self.annotations.items():
                    # Validate image_name (should be a string)
                    if not isinstance(image_name, str):
                        print(f"Warning: Skipping annotations for invalid image_name type: {type(image_name)} (value: {image_name})")
                        continue

                    img_width, img_height = self.get_image_dimensions(image_name, images_folder)
                    if img_width == 0 or img_height == 0: # Avoid division by zero if image dimensions are invalid
                        print(f"Warning: Skipping annotations for image '{image_name}' due to zero image dimensions.")
                        continue
                        
                    for ann in anns:
                        x1, y1, x2, y2 = ann['bbox']
                        # Convert absolute pixel coordinates [x1, y1, x2, y2] to normalized YOLO-like format
                        center_x: float = ((x1 + x2) / 2) / img_width
                        center_y: float = ((y1 + y2) / 2) / img_height
                        width: float = (x2 - x1) / img_width
                        height: float = (y2 - y1) / img_height
                        # Write to file, ensuring all parts are strings
                        f.write(f"{image_name},{ann['class']},{center_x:.6f},{center_y:.6f},{width:.6f},{height:.6f}\n")
        except Exception as e:
            # Provide context if an error occurs during saving
            current_image_name_for_error = image_name if 'image_name' in locals() else "Unknown Image"
            print(f"Error saving annotations for '{current_image_name_for_error}': {e}")

    def load_temp_annotations(self, current_image_name: str):
        """
        Loads annotations for the specified image into the temporary working list.
        These are deep copied to allow modification without affecting the main store
        until explicitly saved.

        Args:
            current_image_name (str): The filename of the image whose annotations are to be loaded.
        """
        self.temp_annotations = [] # Clear any existing temporary annotations
        if current_image_name in self.annotations:
            for ann in self.annotations[current_image_name]:
                self.temp_annotations.append(copy.deepcopy(ann)) # Use deepcopy for safe editing

    def copy_annotation(self, selected_index: int) -> bool:
        """
        Copies the annotation at the given index from `temp_annotations`
        to an internal buffer (`last_copied_annotation`).

        Args:
            selected_index (int): The index of the annotation to copy from `temp_annotations`.

        Returns:
            bool: True if the copy was successful, False otherwise (e.g., invalid index).
        """
        if 0 <= selected_index < len(self.temp_annotations):
            self.last_copied_annotation = copy.deepcopy(self.temp_annotations[selected_index])
            return True
        return False

    def paste_annotation(self, image_width: int, image_height: int) -> Optional[Dict[str, Any]]:
        """
        Pastes the `last_copied_annotation` into `temp_annotations`.
        The pasted annotation is offset slightly and its coordinates are clamped
        to the image boundaries.

        Args:
            image_width (int): The width of the current image, for boundary clamping.
            image_height (int): The height of the current image, for boundary clamping.

        Returns:
            Optional[Dict[str, Any]]: The newly pasted annotation dictionary if successful,
                                      otherwise None.
        """
        if self.last_copied_annotation:
            new_annotation = copy.deepcopy(self.last_copied_annotation)
            
            original_bbox_width = new_annotation['bbox'][2] - new_annotation['bbox'][0]
            original_bbox_height = new_annotation['bbox'][3] - new_annotation['bbox'][1]

            # Apply a small offset to the pasted annotation
            offset_x, offset_y = 20, 20
            new_annotation['bbox'][0] += offset_x
            new_annotation['bbox'][1] += offset_y
            
            # Adjust x2, y2 based on original width/height to maintain size initially
            new_annotation['bbox'][2] = new_annotation['bbox'][0] + original_bbox_width
            new_annotation['bbox'][3] = new_annotation['bbox'][1] + original_bbox_height

            # Clamp coordinates to be within image boundaries
            # Ensure x1 is within bounds, then calculate x2 based on width, then clamp x2.
            new_annotation['bbox'][0] = max(0, min(new_annotation['bbox'][0], image_width - (original_bbox_width if original_bbox_width > 0 else 10) ))
            new_annotation['bbox'][1] = max(0, min(new_annotation['bbox'][1], image_height - (original_bbox_height if original_bbox_height > 0 else 10) ))
            new_annotation['bbox'][2] = min(new_annotation['bbox'][0] + original_bbox_width, image_width)
            new_annotation['bbox'][3] = min(new_annotation['bbox'][1] + original_bbox_height, image_height)
            
            # Ensure minimum size (e.g., 10x10 pixels) if original was too small or became so after clamping
            if new_annotation['bbox'][2] - new_annotation['bbox'][0] < 10:
                new_annotation['bbox'][2] = min(new_annotation['bbox'][0] + 10, image_width)
            if new_annotation['bbox'][3] - new_annotation['bbox'][1] < 10:
                 new_annotation['bbox'][3] = min(new_annotation['bbox'][1] + 10, image_height)
            
            self.temp_annotations.append(new_annotation)
            return new_annotation
        return None

    def get_next_color(self) -> str:
        """
        Provides the next color from the predefined `annotation_colors` list,
        cycling through the list.

        Returns:
            str: The hex color code string.
        """
        color = self.annotation_colors[self.color_index % len(self.annotation_colors)]
        self.color_index += 1 # Increment for next call
        return color

    def add_temp_annotation(self, bbox: List[int], klass: str, color: str) -> Dict[str, Any]:
        """
        Adds a new annotation to the `temp_annotations` list.

        Args:
            bbox (List[int]): The bounding box coordinates [x1, y1, x2, y2].
            klass (str): The class name for the annotation.
            color (str): The color for the annotation.

        Returns:
            Dict[str, Any]: The newly created annotation dictionary.
        """
        annotation: Dict[str, Any] = {
            'class': klass,
            'bbox': bbox,
            'visible': True, # New annotations are visible by default
            'color': color
        }
        self.temp_annotations.append(annotation)
        return annotation

    def update_annotations_for_current_image(self, current_image_name: str):
        """
        Updates the main `annotations` dictionary with the current `temp_annotations`
        for the specified image. Only visible annotations are saved. If no visible
        annotations exist, the entry for the image is removed from `annotations`.

        Args:
            current_image_name (str): The filename of the current image.
        """
        # Filter out any annotations marked as not visible from temp_annotations
        visible_annotations = [ann for ann in self.temp_annotations if ann.get('visible', True)]
        
        if visible_annotations:
            self.annotations[current_image_name] = copy.deepcopy(visible_annotations) # Save a deep copy
        elif current_image_name in self.annotations:
            # If no visible annotations, remove the image entry from the main store
            del self.annotations[current_image_name]
            
    def delete_temp_annotation(self, index: int) -> bool:
        """
        Deletes an annotation from `temp_annotations` at the specified index.

        Args:
            index (int): The index of the annotation to delete.

        Returns:
            bool: True if deletion was successful, False otherwise (e.g., invalid index).
        """
        if 0 <= index < len(self.temp_annotations):
            del self.temp_annotations[index]
            return True
        return False

    def change_temp_annotation_color(self, index: int, new_color: str) -> bool:
        """
        Changes the color of a temporary annotation at the specified index.

        Args:
            index (int): The index of the annotation in `temp_annotations`.
            new_color (str): The new hex color code.

        Returns:
            bool: True if successful, False otherwise (e.g., invalid index).
        """
        if 0 <= index < len(self.temp_annotations):
            self.temp_annotations[index]['color'] = new_color
            return True
        return False

    def update_temp_annotation_class(self, index: int, new_class: str) -> bool:
        """
        Updates the class of a temporary annotation at the specified index.

        Args:
            index (int): The index of the annotation in `temp_annotations`.
            new_class (str): The new class name.

        Returns:
            bool: True if successful, False otherwise (e.g., invalid index).
        """
        if 0 <= index < len(self.temp_annotations):
            self.temp_annotations[index]['class'] = new_class
            return True
        return False

    def get_temp_annotation_at_point(self, x: float, y: float, zoom_factor: float, 
                                     pan_x: float, pan_y: float) -> Optional[int]:
        """
        Finds the index of a temporary annotation at the given image coordinates.
        Checks annotations in reverse order to find the topmost one.

        Args:
            x (float): The x-coordinate on the canvas.
            y (float): The y-coordinate on the canvas.
            zoom_factor (float): The current zoom factor of the canvas.
            pan_x (float): The current horizontal pan offset of the canvas.
            pan_y (float): The current vertical pan offset of the canvas.

        Returns:
            Optional[int]: The index of the annotation if found, otherwise None.
        """
        # Convert canvas coordinates to image coordinates
        img_x = (x - pan_x) / zoom_factor
        img_y = (y - pan_y) / zoom_factor
        
        # Iterate in reverse to get the topmost annotation if overlapping
        for i in reversed(range(len(self.temp_annotations))):
            ann = self.temp_annotations[i]
            if not ann.get('visible', True): # Skip non-visible annotations
                continue
            bbox = ann['bbox']
            if (bbox[0] <= img_x <= bbox[2] and bbox[1] <= img_y <= bbox[3]):
                return i
        return None

    def edit_temp_annotation_bbox(self, index: int, new_bbox_part: Dict[str, float], 
                                  img_width: int, img_height: int):
        """
        Edits a part of a temporary annotation's bounding box (e.g., x1, y1, x2, or y2).
        Ensures the edited bounding box remains within image bounds and maintains a minimum size.

        Args:
            index (int): The index of the annotation in `temp_annotations`.
            new_bbox_part (Dict[str, float]): A dictionary specifying the part of the bbox to update
                                             and its new value (e.g., {'x1': 100.0}).
            img_width (int): The width of the current image.
            img_height (int): The height of the current image.
        """
        if not (0 <= index < len(self.temp_annotations)):
            return # Invalid index

        bbox = self.temp_annotations[index]['bbox']
        original_bbox = bbox.copy() # For reference if a resize operation is invalid

        # Update the specified part of the bounding box
        for key, value in new_bbox_part.items():
            if key == 'x1': bbox[0] = value
            elif key == 'y1': bbox[1] = value
            elif key == 'x2': bbox[2] = value
            elif key == 'y2': bbox[3] = value
            # Ensure coordinates are correctly ordered (x1 < x2, y1 < y2) after partial update
            if 'x1' in new_bbox_part or 'x2' in new_bbox_part:
                bbox[0], bbox[2] = min(bbox[0], bbox[2]), max(bbox[0], bbox[2])
            if 'y1' in new_bbox_part or 'y2' in new_bbox_part:
                bbox[1], bbox[3] = min(bbox[1], bbox[3]), max(bbox[1], bbox[3])


        # Ensure minimum size (e.g., 10 pixels)
        min_size = 10
        if bbox[2] - bbox[0] < min_size:
            # If 'x1' was being dragged, adjust x1; otherwise adjust x2
            if 'x1' in new_bbox_part and new_bbox_part['x1'] > original_bbox[0]: # Dragging left handle to the right
                 bbox[0] = bbox[2] - min_size
            else: # Dragging right handle to the left or other cases
                 bbox[2] = bbox[0] + min_size
        
        if bbox[3] - bbox[1] < min_size:
            # If 'y1' was being dragged, adjust y1; otherwise adjust y2
            if 'y1' in new_bbox_part and new_bbox_part['y1'] > original_bbox[1]: # Dragging top handle downwards
                bbox[1] = bbox[3] - min_size
            else: # Dragging bottom handle upwards or other cases
                bbox[3] = bbox[1] + min_size
        
        # Constrain to image bounds after size adjustment
        bbox[0] = max(0, min(bbox[0], img_width))
        bbox[1] = max(0, min(bbox[1], img_height))
        bbox[2] = max(bbox[0], min(bbox[2], img_width)) # Ensure x2 >= x1
        bbox[3] = max(bbox[1], min(bbox[3], img_height)) # Ensure y2 >= y1

        self.temp_annotations[index]['bbox'] = bbox

    def move_temp_annotation_bbox(self, index: int, dx: float, dy: float, 
                                  img_width: int, img_height: int):
        """
        Moves an entire temporary annotation's bounding box by dx, dy,
        clamping the result to image boundaries.

        Args:
            index (int): The index of the annotation in `temp_annotations`.
            dx (float): The change in x-coordinate.
            dy (float): The change in y-coordinate.
            img_width (int): The width of the current image.
            img_height (int): The height of the current image.
        """
        if not (0 <= index < len(self.temp_annotations)):
            return # Invalid index

        bbox = self.temp_annotations[index]['bbox']
        original_width = bbox[2] - bbox[0]
        original_height = bbox[3] - bbox[1]

        # Calculate new top-left corner
        new_x1 = bbox[0] + dx
        new_y1 = bbox[1] + dy
        
        # Clamp new_x1 and new_y1 to ensure the entire box stays within bounds
        new_x1 = max(0, min(new_x1, img_width - original_width))
        new_y1 = max(0, min(new_y1, img_height - original_height))
        
        # Update all coordinates based on the clamped top-left and original size
        bbox[0] = new_x1
        bbox[1] = new_y1
        bbox[2] = new_x1 + original_width
        bbox[3] = new_y1 + original_height
        
        self.temp_annotations[index]['bbox'] = bbox

    def approve_model_annotations(self, model_annotations: List[Dict[str, Any]]) -> int:
        """
        Converts model-generated annotations to regular temporary annotations.
        Assigns a color if not provided by the model.

        Args:
            model_annotations (List[Dict[str, Any]]): A list of annotation dictionaries
                                                      from the AI model.

        Returns:
            int: The number of annotations successfully approved and added.
        """
        num_approved = 0
        for ann in model_annotations:
            new_ann = copy.deepcopy(ann)
            new_ann.pop('is_model_annotation', None) # Remove model-specific flag
            new_ann.pop('confidence', None)        # Remove confidence score
            
            # Assign a default color if the model annotation doesn't have one
            if 'color' not in new_ann or new_ann['color'] is None: 
                new_ann['color'] = self.get_next_color()
            
            new_ann['visible'] = True # Approved annotations are visible by default
            self.temp_annotations.append(new_ann)
            num_approved +=1
        return num_approved

    def clear_temp_annotations(self):
        """Clears all annotations from the temporary list."""
        self.temp_annotations = []
        # Optionally, reset color_index if desired when clearing annotations for a new image.
        # self.color_index = 0
        
    def toggle_temp_annotation_visibility(self, index: int) -> bool:
        """
        Toggles the 'visible' state of a temporary annotation.

        Args:
            index (int): The index of the annotation in `temp_annotations`.

        Returns:
            bool: True if the visibility was toggled successfully, False otherwise.
        """
        if 0 <= index < len(self.temp_annotations):
            # Default to True if 'visible' key doesn't exist, then toggle
            self.temp_annotations[index]['visible'] = not self.temp_annotations[index].get('visible', True)
            return True
        return False
