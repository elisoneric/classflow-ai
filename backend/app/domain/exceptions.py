class DomainError(Exception):
    """Base class for all domain-level errors."""


class NotFoundError(DomainError):
    def __init__(self, entity: str, identifier: object):
        super().__init__(f"{entity} not found: {identifier}")
        self.entity = entity
        self.identifier = identifier


class InvalidStateTransitionError(DomainError):
    def __init__(self, entity: str, current_state: str, attempted_action: str):
        super().__init__(
            f"Cannot {attempted_action} on {entity} while in state {current_state}"
        )


class UnsupportedContactMethodError(DomainError):
    """Raised when WHATSAPP (or any not-yet-implemented channel) is selected. See ADR-1."""

    def __init__(self, method: str):
        super().__init__(f"Contact method not yet supported: {method}")


class ConflictError(DomainError):
    """Raised for uniqueness violations or other state conflicts that aren't a status transition."""


class ValidationError(DomainError):
    """Raised for cross-field business rule violations that Pydantic's field-level validation can't express."""
