export class ArogyaError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }
}

export class InvalidRecordTypeError extends ArogyaError {
  constructor(message: string = 'Invalid record type specified') {
    super(message);
  }
}

export class FutureDateError extends ArogyaError {
  constructor(message: string = 'Date cannot be in the future') {
    super(message);
  }
}

export class FileSizeLimitError extends ArogyaError {
  constructor(message: string = 'File size exceeds limit') {
    super(message);
  }
}

export class UnsupportedFileTypeError extends ArogyaError {
  constructor(message: string = 'Unsupported file type') {
    super(message);
  }
}

export class OCRExtractionError extends ArogyaError {
  constructor(message: string = 'OCR extraction failed or text is empty') {
    super(message);
  }
}

export class InvalidParameterValueError extends ArogyaError {
  constructor(message: string = 'Invalid parameter value') {
    super(message);
  }
}

export class MissingUnitError extends ArogyaError {
  constructor(message: string = 'Parameter unit is missing') {
    super(message);
  }
}

export class EmptyReminderTitleError extends ArogyaError {
  constructor(message: string = 'Reminder title cannot be empty') {
    super(message);
  }
}

export class InvalidDueDateError extends ArogyaError {
  constructor(message: string = 'Reminder due date is invalid or too far in the future') {
    super(message);
  }
}

export class InvalidRecurrenceError extends ArogyaError {
  constructor(message: string = 'Invalid recurrence interval') {
    super(message);
  }
}

export class ShareTokenExpiredError extends ArogyaError {
  constructor(message: string = 'The shared token has expired or is invalid') {
    super(message);
  }
}

export class InsufficientDataError extends ArogyaError {
  constructor(message: string = 'Insufficient data to complete operation') {
    super(message);
  }
}
