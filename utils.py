"""
Provides utility classes for the AI Annotation Tool.

Currently, this module includes an UndoRedoManager for managing state history
and enabling undo/redo functionality.
"""
import copy
from typing import List, Any, Optional, Dict

class UndoRedoManager:
    """
    Manages undo and redo operations by keeping a history of states.

    Attributes:
        history (List[Any]): A list storing deep copies of states.
        current_index (int): An integer pointing to the current state in the history.
        max_history (int): The maximum number of states to keep in history.
    """
    def __init__(self, max_history: int = 50):
        """
        Initializes the UndoRedoManager.

        Args:
            max_history (int, optional): The maximum number of history states to store.
                                         Defaults to 50.
        """
        self.history: List[Any] = []
        self.current_index: int = -1  # Points to the last saved state index
        self.max_history: int = max_history
    
    def save_state(self, state: Any):
        """
        Saves the current state to the history.

        If new states are added after an undo operation (i.e., current_index is not
        at the end of the history), subsequent states (redo history) are cleared.
        If the history exceeds max_history, the oldest state is removed.

        Args:
            state (Any): The state to save. A deep copy of the state is stored.
                         The state should be a dictionary or an object that supports deepcopy.
        """
        # If we have undone actions and then make a new action,
        # the previous "redo" states are no longer valid.
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(copy.deepcopy(state))
        self.current_index += 1
        
        # Enforce history limit
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1 # Adjust index as the list was shortened from the beginning
    
    def undo(self) -> Optional[Any]:
        """
        Reverts to the previous state in the history.

        Returns:
            Optional[Any]: The previous state if an undo operation can be performed, 
                           otherwise None. Returns a deep copy of the state.
        """
        if self.can_undo():
            # Current index points to the *current* state. Undo means going to current_index - 1.
            # However, save_state increments current_index *after* appending.
            # So, if current_index is 0, it's the first saved state. We can't undo further than that.
            # If current_index is > 0, we can move back.
            self.current_index -= 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def redo(self) -> Optional[Any]:
        """
        Re-applies the next state in the history that was previously undone.

        Returns:
            Optional[Any]: The next state if a redo operation can be performed,
                           otherwise None. Returns a deep copy of the state.
        """
        if self.can_redo():
            self.current_index += 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def can_undo(self) -> bool:
        """
        Checks if an undo operation can be performed.

        Returns:
            bool: True if undo is possible, False otherwise.
        """
        # If current_index is 0, it means we are at the very first state saved.
        # We can only undo if current_index is greater than 0, meaning there's a previous state.
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """
        Checks if a redo operation can be performed.

        Returns:
            bool: True if redo is possible, False otherwise.
        """
        # We can redo if current_index is less than the last actual index in history.
        return self.current_index < len(self.history) - 1
