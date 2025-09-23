class GlobalState:
    def __init__(self):
        self.dashboard_visible = True
    
    def toggle_visible(self):
        self.dashboard_visible = not self.dashboard_visible
        
    def set_visible(self, state):
        self.dashboard_visible = state
        
global_state = GlobalState()