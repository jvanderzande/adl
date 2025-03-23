class GetEbookException(Exception):
    def __init__(self, filepath:str, message:str):
        super().__init__(f"Could not get ebook {filepath} - {message}")

class DataDirectoryAccessError(Exception):
    def __init__(self):
        super().__init__("Error accessing data directory!")