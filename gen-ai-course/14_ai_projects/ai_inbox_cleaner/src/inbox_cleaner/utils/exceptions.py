class InboxCleanerException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class GmailIntegrationError(InboxCleanerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)

class SlackIntegrationError(InboxCleanerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)

class LLMClassificationError(InboxCleanerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class LLMDraftError(InboxCleanerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
