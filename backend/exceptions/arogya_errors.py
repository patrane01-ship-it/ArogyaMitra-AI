"""
ArogyaMitra AI - Custom Exceptions
All custom exceptions inherit from ArogyaError base class.
Per FEATURES.md §4.
"""


class ArogyaError(Exception):
    """Base exception for all ArogyaMitra errors."""
    
    def __init__(self, message: str, status_code: int = 500, field: str = None):
        self.message = message
        self.status_code = status_code
        self.field = field
        self.error_code = self.__class__.__name__
        super().__init__(self.message)


# ── Record Validation Errors ───────────────────────────────
class InvalidRecordTypeError(ArogyaError):
    """Raised when record_type is not a valid enum value."""
    def __init__(self, message: str = "Invalid record type"):
        super().__init__(message, status_code=400, field="record_type")


class FutureDateError(ArogyaError):
    """Raised when report_date is in the future."""
    def __init__(self, message: str = "Report date cannot be in the future"):
        super().__init__(message, status_code=400, field="report_date")


class FileSizeLimitError(ArogyaError):
    """Raised when uploaded file exceeds size limit."""
    def __init__(self, message: str = "File size exceeds 10MB limit"):
        super().__init__(message, status_code=413, field="file")


class UnsupportedFileTypeError(ArogyaError):
    """Raised when uploaded file has unsupported MIME type."""
    def __init__(self, message: str = "Unsupported file type"):
        super().__init__(message, status_code=400, field="file_type")


class OCRExtractionError(ArogyaError):
    """Raised when OCR fails to extract sufficient text."""
    def __init__(self, message: str = "OCR extraction failed or produced insufficient text"):
        super().__init__(message, status_code=422)


# ── Parameter Validation Errors ────────────────────────────
class InvalidParameterValueError(ArogyaError):
    """Raised when a clinical parameter value is invalid."""
    def __init__(self, message: str = "Invalid parameter value"):
        super().__init__(message, status_code=422, field="value")


class MissingUnitError(ArogyaError):
    """Raised when unit is missing or empty."""
    def __init__(self, message: str = "Unit cannot be empty"):
        super().__init__(message, status_code=422, field="unit")


# ── Reminder Validation Errors ─────────────────────────────
class EmptyReminderTitleError(ArogyaError):
    """Raised when reminder title is too short."""
    def __init__(self, message: str = "Reminder title must be at least 3 characters"):
        super().__init__(message, status_code=422, field="title")


class InvalidDueDateError(ArogyaError):
    """Raised when reminder due_date is invalid."""
    def __init__(self, message: str = "Invalid due date"):
        super().__init__(message, status_code=422, field="due_date")


class InvalidRecurrenceError(ArogyaError):
    """Raised when recurrence is not a valid enum value."""
    def __init__(self, message: str = "Invalid recurrence value"):
        super().__init__(message, status_code=422, field="recurrence")


# ── Share Token Errors ─────────────────────────────────────
class ShareTokenExpiredError(ArogyaError):
    """Raised when share token has expired."""
    def __init__(self, message: str = "Share link has expired"):
        super().__init__(message, status_code=410)


class InvalidShareTokenError(ArogyaError):
    """Raised when share token is invalid."""
    def __init__(self, message: str = "Invalid share token"):
        super().__init__(message, status_code=401)


# ── Data Errors ────────────────────────────────────────────
class InsufficientDataError(ArogyaError):
    """Raised when insufficient data exists for an operation."""
    def __init__(self, message: str = "Insufficient data to complete operation"):
        super().__init__(message, status_code=400)


class RecordNotFoundError(ArogyaError):
    """Raised when a record is not found."""
    def __init__(self, message: str = "Record not found"):
        super().__init__(message, status_code=404)


# ── Security Errors ────────────────────────────────────────
class PromptInjectionDetectedError(ArogyaError):
    """Raised when prompt injection is detected."""
    def __init__(self, message: str = "Document contains content that cannot be processed"):
        super().__init__(message, status_code=400)


class GuardrailViolationError(ArogyaError):
    """Raised when LLM output violates critical safety guardrails."""
    def __init__(self, message: str = "Output blocked by guardrail"):
        super().__init__(message, status_code=422)


class AuthenticationError(ArogyaError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(ArogyaError):
    """Raised when authorization fails (user doesn't have permission)."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


# ── Database Errors ────────────────────────────────────────
class DatabaseError(ArogyaError):
    """Raised when a database operation fails."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=503)


class RecordAlreadyExistsError(ArogyaError):
    """Raised when attempting to create a duplicate record."""
    def __init__(self, message: str = "Record already exists"):
        super().__init__(message, status_code=409)
