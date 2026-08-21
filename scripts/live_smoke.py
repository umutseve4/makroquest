"""Canlı deploy smoke testi.

Kullanım: python scripts/live_smoke.py [BASE_URL]
Varsayılan hedef: https://makroquest.onrender.com

Kontroller:
  1. GET  /health                    -> 200, {"status": "ok"}
  2. GET  /case                      -> 200, kasim-2021 listede
  3. POST /case/kasim-2021/start     -> 200, session_id döner
  4. POST /case/session/{sid}/answer -> 200 (q1 cevaplanır)
  5. GET  /case/session/{sid}/score  -> 200, total_earned alanı var
  6. GET  /retrieve?q=...&k=3        -> 200, >=1 sonuç
  7. POST /ask                       -> 200, >=1 citation
  8. GET  /                          -> 3xx redirect, Location tam olarak /docs

Not: FAIL alınırsa https://status.render.com kontrol edilmeli; platform
incident'ları (ör. 2026-08-20 free-tier spin-up kesintisi) 502/503/429 üretir.
root-redirect kontrolü, kök redirect'i içeren main commit'inin canlıya
deploy edilmiş olmasını gerektirir.

Çıkış kodu: hepsi PASS ise 0, aksi halde 1.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://makroquest.onrender.com"
TIMEOUT = 60


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """3xx yanıtı takip etme — status + Location header'ını olduğu gibi döndür."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "makroquest-live-smoke"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:  # 4xx/5xx: status + gövdeyi raporla, çökme
        raw = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, raw


def get(path: str) -> tuple[int, object]:
    return _request("GET", path)


def post(path: str, body: dict) -> tuple[int, object]:
    return _request("POST", path, body)


def get_no_redirect(path: str) -> tuple[int, str]:
    """GET isteği at, redirect'i takip etme; (status, Location) döndür."""
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "makroquest-live-smoke"},
        method="GET",
    )
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as exc:  # 3xx buraya düşer (redirect takip edilmedi)
        return exc.code, exc.headers.get("Location", "")


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    # Render free tier uykudan uyanabilir: /health'i 5 denemeye kadar bekle.
    status, body = 0, {}
    for attempt in range(5):
        try:
            status, body = get("/health")
        except urllib.error.URLError:
            status, body = 0, {}
        if status == 200:
            break
        if attempt < 4:
            time.sleep(20)
    ok = status == 200 and isinstance(body, dict) and body.get("status") == "ok"
    results.append(("health", ok, f"{status} {body}"))

    status, body = get("/case")
    items = body if isinstance(body, list) else []
    case_ids = [c.get("case_id") or c.get("id") for c in items if isinstance(c, dict)]
    ok = status == 200 and "kasim-2021" in case_ids
    results.append(("case-list", ok, f"{status} {case_ids}"))

    status, body = post("/case/kasim-2021/start", {})
    sid = body.get("session_id") if isinstance(body, dict) else None
    results.append(("case-start", status == 200 and bool(sid), f"{status} session={bool(sid)}"))

    status, body = post(
        f"/case/session/{sid}/answer",
        {"question_id": "q1", "choice_index": 0},
    )
    results.append(("case-answer", status == 200, f"{status}"))

    status, body = get(f"/case/session/{sid}/score")
    earned = body.get("total_earned") if isinstance(body, dict) else None
    ok = status == 200 and isinstance(earned, int)
    results.append(("case-score", ok, f"{status} total_earned={earned}"))

    status, body = get("/retrieve?q=enflasyon%20neden%20artti&k=3")
    n = len(body.get("results", [])) if isinstance(body, dict) else 0
    results.append(("retrieve", status == 200 and n >= 1, f"{status} n={n}"))

    status, body = post("/ask", {"question": "Kasim 2021'de TL neden deger kaybetti?", "k": 3})
    cites = len(body.get("citations", [])) if isinstance(body, dict) else 0
    results.append(("ask", status == 200 and cites >= 1, f"{status} citations={cites}"))

    status, location = get_no_redirect("/")
    ok = status in (301, 302, 303, 307, 308) and location.rstrip("/") == "/docs"
    results.append(("root-redirect", ok, f"{status} location={location!r}"))

    print("===== OTOMATIK KONTROL =====")
    all_ok = True
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail[:300]}")
        all_ok = all_ok and ok
    print("SONUC:", "PASS" if all_ok else "FAIL", f"({BASE})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
