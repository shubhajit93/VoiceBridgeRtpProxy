# Define a custom exception for no available ports
class NoPortAvailableException(Exception):
    def __init__(self, message="No available ports"):
        self.message = message
        super().__init__(self.message)
