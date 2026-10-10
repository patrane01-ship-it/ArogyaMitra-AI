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


# ── Phase 2: Auth Errors ───────────────────────────────────
class InvalidEmailError(ArogyaError):
    def __init__(self, message: str = "Invalid email format"):
        super().__init__(message, status_code=422, field="email")


class WeakPasswordError(ArogyaError):
    def __init__(self, message: str = "Password must be at least 8 characters with at least 1 number and 1 uppercase letter"):
        super().__init__(message, status_code=422, field="password")


class InvalidNameError(ArogyaError):
    def __init__(self, message: str = "Name must be at least 2 characters"):
        super().__init__(message, status_code=422, field="full_name")


class FutureDateOfBirthError(ArogyaError):
    def __init__(self, message: str = "Date of birth cannot be in the future"):
        super().__init__(message, status_code=422, field="date_of_birth")


class EmailAlreadyExistsError(ArogyaError):
    def __init__(self, message: str = "An account with this email already exists"):
        super().__init__(message, status_code=409, field="email")


class InvalidCredentialsError(ArogyaError):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, status_code=401)


class InvalidTokenError(ArogyaError):
    def __init__(self, message: str = "Invalid or tampered token"):
        super().__init__(message, status_code=401)


class TokenExpiredError(ArogyaError):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, status_code=401)


class UserNotFoundError(ArogyaError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, status_code=404)


# ── Phase 2: ML Errors ─────────────────────────────────────
class InvalidFeatureVectorError(ArogyaError):
    def __init__(self, message: str = "Feature vector must contain exactly 15 valid numeric values"):
        super().__init__(message, status_code=422)


class ModelNotFoundError(ArogyaError):
    def __init__(self, message: str = "Requested ML model not found"):
        super().__init__(message, status_code=404)


class ModelLoadError(ArogyaError):
    def __init__(self, message: str = "Failed to load ML model artifact"):
        super().__init__(message, status_code=500)


class InvalidContaminationError(ArogyaError):
    def __init__(self, message: str = "Contamination factor must be between 0.01 and 0.5"):
        super().__init__(message, status_code=422)


class InsufficientDataForAnomalyError(ArogyaError):
    def __init__(self, message: str = "At least 3 readings required for anomaly detection"):
        super().__init__(message, status_code=400)


class InsufficientVarianceError(ArogyaError):
    def __init__(self, message: str = "Insufficient variance in readings for anomaly calculation"):
        super().__init__(message, status_code=400)


# ── Phase 2: Drug Interaction Errors ───────────────────────
class SameDrugInteractionError(ArogyaError):
    def __init__(self, message: str = "Drug interaction cannot be evaluated on identical drugs"):
        super().__init__(message, status_code=422)


class UnrecognizedDrugError(ArogyaError):
    def __init__(self, message: str = "Drug name could not be resolved"):
        super().__init__(message, status_code=422)


class InvalidSeverityError(ArogyaError):
    def __init__(self, message: str = "Invalid interaction severity level"):
        super().__init__(message, status_code=422)


# ── Phase 3: Family Profile Errors ────────────────────────────
class CannotDeletePrimaryProfileError(ArogyaError):
    def __init__(self, message: str = "Cannot delete or deactivate your primary (SELF) profile"):
        super().__init__(message, status_code=400)


class FamilyMemberLimitError(ArogyaError):
    def __init__(self, message: str = "Family member limit reached for your subscription tier"):
        super().__init__(message, status_code=403)


class InvalidABHAIDError(ArogyaError):
    def __init__(self, message: str = "ABHA ID must be exactly 14 numeric digits"):
        super().__init__(message, status_code=422, field="abha_id")


class FamilyProfileNotFoundError(ArogyaError):
    def __init__(self, message: str = "Family profile not found"):
        super().__init__(message, status_code=404)


# ── Phase 3: ABDM / FHIR Errors ───────────────────────────────
class ABDMAuthError(ArogyaError):
    def __init__(self, message: str = "ABDM authentication failed"):
        super().__init__(message, status_code=401)


class ABDMSyncCooldownError(ArogyaError):
    def __init__(self, message: str = "ABDM sync allowed only once every 24 hours"):
        super().__init__(message, status_code=429)


class FHIRParseError(ArogyaError):
    def __init__(self, message: str = "Failed to parse FHIR resource"):
        super().__init__(message, status_code=422)


# ── Phase 3: Prediction Errors ─────────────────────────────────
class InsufficientDataForPredictionError(ArogyaError):
    def __init__(self, message: str = "At least 3 readings required to compute a health trend prediction"):
        super().__init__(message, status_code=400)


class VolatileTrendError(ArogyaError):
    def __init__(self, message: str = "Trend is too volatile (R² < 0.40) to make a reliable prediction"):
        super().__init__(message, status_code=422)


# ── Phase 3: Doctor Workspace Errors ──────────────────────────
class WorkspaceAccessExpiredError(ArogyaError):
    def __init__(self, message: str = "This doctor workspace link has expired"):
        super().__init__(message, status_code=410)


class WorkspaceNotFoundError(ArogyaError):
    def __init__(self, message: str = "Doctor workspace not found"):
        super().__init__(message, status_code=404)


# ── Phase 3: WhatsApp Bot Errors ───────────────────────────────
class InvalidPhoneNumberError(ArogyaError):
    def __init__(self, message: str = "Phone number must be in E.164 format (e.g. +919876543210)"):
        super().__init__(message, status_code=422, field="phone_number")


class OTPExpiredError(ArogyaError):
    def __init__(self, message: str = "OTP has expired. Please request a new one"):
        super().__init__(message, status_code=401)


class BotRateLimitError(ArogyaError):
    def __init__(self, message: str = "Too many messages. Please wait before sending again"):
        super().__init__(message, status_code=429)


class InvalidWebhookSignatureError(ArogyaError):
    def __init__(self, message: str = "Webhook signature verification failed"):
        super().__init__(message, status_code=401)


# ── Phase 3: Wearable Errors ───────────────────────────────────
class WearableAuthError(ArogyaError):
    def __init__(self, message: str = "Wearable device OAuth authentication failed"):
        super().__init__(message, status_code=401)


class WearableSyncError(ArogyaError):
    def __init__(self, message: str = "Wearable data sync failed"):
        super().__init__(message, status_code=502)


# ── Phase 3: Subscription / Payment Errors ─────────────────────
class PaymentVerificationError(ArogyaError):
    def __init__(self, message: str = "Payment signature verification failed"):
        super().__init__(message, status_code=400)


class FeatureNotAvailableError(ArogyaError):
    def __init__(self, message: str = "This feature is not available on your current subscription tier"):
        super().__init__(message, status_code=403)


class SubscriptionNotFoundError(ArogyaError):
    def __init__(self, message: str = "No active subscription found"):
        super().__init__(message, status_code=404)


# ── Phase 3: API Key Errors ────────────────────────────────────
class APIKeyNotFoundError(ArogyaError):
    def __init__(self, message: str = "API key not found or inactive"):
        super().__init__(message, status_code=401)


class APIRateLimitError(ArogyaError):
    def __init__(self, message: str = "API rate limit exceeded"):
        super().__init__(message, status_code=429)


class ConsentNotGrantedError(ArogyaError):
    def __init__(self, message: str = "Patient has not granted consent for this API key to access their data"):
        super().__init__(message, status_code=403)


# ── Phase 3: Voice Input Errors ────────────────────────────────
class AudioTooLongError(ArogyaError):
    def __init__(self, message: str = "Audio recording exceeds the maximum duration of 60 seconds"):
        super().__init__(message, status_code=413)


class AudioFileTooLargeError(ArogyaError):
    def __init__(self, message: str = "Audio file size exceeds the 25MB limit"):
        super().__init__(message, status_code=413)


class UnsupportedAudioFormatError(ArogyaError):
    def __init__(self, message: str = "Unsupported audio format. Supported: webm, mp3, mp4, wav"):
        super().__init__(message, status_code=400, field="audio_format")


class TranscriptionFailedError(ArogyaError):
    def __init__(self, message: str = "Audio transcription failed. Please re-record or speak more clearly"):
        super().__init__(message, status_code=422)
