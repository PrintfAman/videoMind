import shutil
import pytest

from app.services import media


def test_find_executable_missing(monkeypatch):
    # Make shutil.which return None
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        media._find_executable("ffprobe")
