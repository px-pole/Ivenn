import pytest

from app.core.storage import (
    FileTooLargeError,
    MAX_UPLOAD_SIZE_BYTES,
    UnsupportedFileTypeError,
    delete_file,
    resolve_path,
    save_file,
)


def test_save_file_writes_content_and_returns_generated_key(storage_dir):
    storage_key = save_file(content=b"hello", original_filename="receipt.pdf", mime_type="application/pdf")

    assert storage_key.endswith(".pdf")
    assert resolve_path(storage_key).read_bytes() == b"hello"


def test_save_file_ignores_client_supplied_path(storage_dir):
    storage_key = save_file(
        content=b"data", original_filename="../../etc/passwd.png", mime_type="image/png"
    )

    assert "/" not in storage_key
    assert ".." not in storage_key
    assert resolve_path(storage_key).parent == storage_dir


def test_save_file_rejects_unsupported_mime_type(storage_dir):
    with pytest.raises(UnsupportedFileTypeError):
        save_file(content=b"data", original_filename="script.exe", mime_type="application/x-msdownload")


def test_save_file_rejects_oversized_content(storage_dir):
    with pytest.raises(FileTooLargeError):
        save_file(
            content=b"x" * (MAX_UPLOAD_SIZE_BYTES + 1),
            original_filename="big.png",
            mime_type="image/png",
        )


def test_delete_file_removes_stored_content(storage_dir):
    storage_key = save_file(content=b"hello", original_filename="a.jpg", mime_type="image/jpeg")
    assert resolve_path(storage_key).exists()

    delete_file(storage_key)

    assert not resolve_path(storage_key).exists()
