"""Make sure the raw listings file for a city is in the Volume.

Databricks Free Edition restricts outbound internet, so we try the download and,
if it is blocked, expect the file to have been uploaded to the Volume by hand.
"""
from __future__ import annotations

import os
import shutil
import urllib.request
from typing import Callable

from airbnb.config import CityConfig, listings_url
from airbnb.paths import raw_file


class RawFileMissing(RuntimeError):
    pass


def _http_download(url: str, dest: str, timeout: int = 120) -> None:
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "isd-airbnb-pipeline"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def ensure_raw_file(
    c: CityConfig, volume_root: str, download: Callable[[str, str], None] = _http_download
) -> str:
    path = raw_file(volume_root, c)
    if os.path.exists(path):
        return path
    url = listings_url(c)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        download(url, path)
    except Exception as e:  # network blocked, 404, timeout...
        if os.path.exists(path):
            os.remove(path)
        raise RawFileMissing(
            f"Raw file for '{c.name}' is not in the Volume and the download failed ({type(e).__name__}: {e}).\n"
            f"Download it manually from:\n  {url}\n"
            f"and upload it to:\n  {path}"
        ) from e
    if not os.path.exists(path):
        raise RawFileMissing(f"Download reported success but {path} does not exist (source: {url})")
    return path
