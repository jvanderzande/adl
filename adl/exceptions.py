class GetEbookException(Exception):
    def __init__(self, filepath:str, message:str):
        super().__init__(f"Could not get ebook {filepath} - {message}")