class PrinterStatus:
    def __init__(self):
        self.is_printing = False
        self.progress = 0.0

    def update_status(self, data):
        if 'state' in data:
            self.is_printing = data['state'] == 'Printing'
        if 'progress' in data:
            self.progress = data['progress'].get('completion', 0.0)

    def reset_status(self):
        self.is_printing = False
        self.progress = 0.0