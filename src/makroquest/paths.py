"""Veri dizini çözümü — repo checkout'u ve konteyner kurulumu için tek kaynak.

Öncelik sırası:
1. ``MAKROQUEST_DATA_DIR`` ortam değişkeni (Docker/deploy bunu ayarlar).
2. Repo köküne göre ``data/`` (editable kurulum ve CI checkout'u).

Neden: paket wheel olarak site-packages'a kurulduğunda ``__file__``
tabanlı ``parents[N]`` yolu repo kökünü bulamaz (M1.3'ten beri bilinen
sınır). Ortam değişkeni bu bağı koparır.
"""

from __future__ import annotations

import os
from pathlib import Path

_REPO_DATA = Path(__file__).resolve().parents[2] / "data"

ENV_VAR = "MAKROQUEST_DATA_DIR"


def data_dir() -> Path:
    """Aktif veri dizinini döndür (env override > repo-göreli varsayılan)."""
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        return Path(env)
    return _REPO_DATA
