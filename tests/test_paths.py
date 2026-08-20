"""MAKROQUEST_DATA_DIR çözümü testleri (M1.7 — wheel kurulumu kırılganlığı fixi)."""

from __future__ import annotations

import os
from pathlib import Path

from makroquest import paths


def test_default_points_to_repo_data() -> None:
    old = os.environ.pop(paths.ENV_VAR, None)
    try:
        d = paths.data_dir()
        assert (d / "corpus").is_dir()
        assert (d / "cases").is_dir()
    finally:
        if old is not None:
            os.environ[paths.ENV_VAR] = old


def test_env_override_wins(tmp_path: Path) -> None:
    old = os.environ.get(paths.ENV_VAR)
    try:
        os.environ[paths.ENV_VAR] = str(tmp_path)
        assert paths.data_dir() == tmp_path
    finally:
        if old is None:
            os.environ.pop(paths.ENV_VAR, None)
        else:
            os.environ[paths.ENV_VAR] = old
