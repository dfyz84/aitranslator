from src.providers.powerpoint import PowerPointProvider


def test_find_soffice_returns_existing_default_path(monkeypatch):
    monkeypatch.setattr("src.providers.powerpoint.shutil.which", lambda _: None)

    def fake_exists(path: str) -> bool:
        return path == r"C:\Program Files\LibreOffice\program\soffice.exe"

    monkeypatch.setattr("src.providers.powerpoint.os.path.exists", fake_exists)

    assert (
        PowerPointProvider._find_soffice()
        == r"C:\Program Files\LibreOffice\program\soffice.exe"
    )
