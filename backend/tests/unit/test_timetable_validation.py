from datetime import time

import pytest

from app.application.timetable.service import _validate_timing
from app.domain.exceptions import ValidationError


def test_end_time_must_be_after_start_time():
    with pytest.raises(ValidationError, match="end_time"):
        _validate_timing(time(16, 0), time(15, 0), time(12, 0), 60, 1, 30)


def test_reminder_time_must_be_at_or_before_start_time():
    with pytest.raises(ValidationError, match="reminder_time"):
        _validate_timing(time(16, 0), time(18, 0), time(16, 30), 60, 1, 30)


def test_reminder_time_equal_to_start_time_is_allowed():
    _validate_timing(time(16, 0), time(18, 0), time(16, 0), 60, 1, 30)  # no raise


def test_response_deadline_must_be_positive():
    with pytest.raises(ValidationError, match="response_deadline_minutes"):
        _validate_timing(time(16, 0), time(18, 0), time(12, 0), 0, 1, 30)


def test_negative_retry_attempts_rejected():
    with pytest.raises(ValidationError, match="retry_attempts"):
        _validate_timing(time(16, 0), time(18, 0), time(12, 0), 60, -1, 30)


def test_retry_interval_required_when_retries_configured():
    with pytest.raises(ValidationError, match="retry_interval_minutes"):
        _validate_timing(time(16, 0), time(18, 0), time(12, 0), 60, 1, 0)


def test_zero_retry_attempts_does_not_require_interval():
    _validate_timing(time(16, 0), time(18, 0), time(12, 0), 60, 0, 0)  # no raise
