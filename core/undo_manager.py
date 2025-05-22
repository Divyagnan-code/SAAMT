import copy

class UndoRedoManager:
    """Manages undo/redo operations"""
    def __init__(self, max_history=50):
        self.history = []
        self.current_index = -1
        self.max_history = max_history
    
    def save_state(self, state):
        """Save current state"""
        # Remove any future history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(copy.deepcopy(state))
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def undo(self):
        """Undo last operation"""
        if self.current_index > 0:
            self.current_index -= 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def redo(self):
        """Redo next operation"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return copy.deepcopy(self.history[self.current_index])
        return None
    
    def can_undo(self):
        return self.current_index > 0
    
    def can_redo(self):
        return self.current_index < len(self.history) - 1
