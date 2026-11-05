import zipfile
from pathlib import Path

import windows_signing


def test_a_zip_with_programs_inside_is_rebuilt_with_the_signed_copies(tmp_path, monkeypatch):
    path = tmp_path / "formvis-portable.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("formvis/formvis.exe", b"unsigned")
        archive.writestr("formvis/readme.txt", b"text")
    monkeypatch.setattr(windows_signing, "is_signed", lambda signtool, file: False)
    monkeypatch.setattr(windows_signing, "sign_file", lambda args, file: Path(file).write_bytes(b"signed"))
    assert windows_signing.sign_zip([], tmp_path / "signtool.exe", path) is True
    with zipfile.ZipFile(path) as archive:
        assert archive.read("formvis/formvis.exe") == b"signed"
        assert archive.read("formvis/readme.txt") == b"text"
