class GlobalCallback:
    def __init__(self):
        self.callbacks = {}
        self.last_id = 0

    def create_callback(self, name):
        if name not in self.callbacks.keys():
            self.callbacks[name] = {}
            
    def attach_to_callback(self, name, callable):
        if name in self.callbacks.keys():
            self.last_id += 1
            self.callbacks[name][f'{self.last_id}'] = callable
            return self.last_id
            
    def detach_from_callback(self, name, id):
        if name in self.callbacks.keys():
            if id in self.callbacks[name].keys():
                del(self.callbacks[name][id])
            
    def call_callback(self, name, *args):
        if name in self.callbacks.keys():
            for callable in self.callbacks[name].keys():
                self.callbacks[name][f'{callable}'](*args)

global_callback_manager = GlobalCallback()
