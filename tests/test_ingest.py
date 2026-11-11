import pytest

from airbnb.ingest import RawFileMissing, ensure_raw_file
from airbnb.paths import raw_file


def test_raw_file_layout(madrid):
    assert raw_file("/Volumes/workspace/airbnb/raw", madrid) == (
        "/Volumes/workspace/airbnb/raw/madrid/2026-09-17/listings.csv.gz"
    )


def test_existing_file_skips_download(tmp_path, madrid):
    p = tmp_path / "madrid" / "2026-09-17" / "listings.csv.gz"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x")

    def download(url, dest):
        raise AssertionError("download must not be called when the file exists")

    assert ensure_raw_file(madrid, str(tmp_path), download=download) == str(p)


def test_download_fallback_used(tmp_path, madrid):
    calls = []

    def download(url, dest):
        calls.append(url)
        with open(dest, "wb") as f:
            f.write(b"x")

    path = ensure_raw_file(madrid, str(tmp_path), download=download)
    assert calls == ["https://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/2026-09-17/data/listings.csv.gz"]
    assert open(path, "rb").read() == b"x"


def test_missing_file_and_blocked_download_raises_with_path_and_url(tmp_path, madrid):
    def download(url, dest):
        raise OSError("Network is unreachable")

    with pytest.raises(RawFileMissing) as e:
        ensure_raw_file(madrid, str(tmp_path), download=download)
    msg = str(e.value)
    assert str(tmp_path / "madrid" / "2026-09-17" / "listings.csv.gz") in msg
    assert "https://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/2026-09-17/data/listings.csv.gz" in msg
    assert not (tmp_path / "madrid" / "2026-09-17" / "listings.csv.gz").exists()
