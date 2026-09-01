import pytest

from app.core.config import Settings


def test_secret_key_must_be_at_least_32_characters():
    with pytest.raises(ValueError):
        Settings(secret_key="short")


def test_secret_key_default_is_long_enough():
    settings = Settings()
    assert len(settings.secret_key) >= 32
