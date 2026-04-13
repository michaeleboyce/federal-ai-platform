"""Download public evidence documents listed in audit/research/public_evidence_sources.csv."""

from __future__ import annotations

import csv
import mimetypes
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "audit" / "research" / "public_evidence_sources.csv"
DOWNLOAD_DIR = ROOT / "audit" / "downloads"
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def infer_extension(url: str, content_type: str) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    return guessed or ".html"


def safe_name(s: str) -> str:
    chars = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            chars.append(ch)
        else:
            chars.append("_")
    return "".join(chars).strip("_")


def download_one(slug: str, url: str) -> tuple[str, str, int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CodexAudit/1.0)",
        },
    )
    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
        content = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        ext = infer_extension(resp.geturl(), content_type)
        out_path = DOWNLOAD_DIR / f"{safe_name(slug)}{ext}"
        out_path.write_bytes(content)
        return resp.geturl(), content_type, len(content), str(out_path)


def main() -> int:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    for row in rows:
        slug = row["slug"].strip()
        url = row["url"].strip()
        try:
            final_url, content_type, nbytes, out_path = download_one(slug, url)
            print(f"OK,{slug},{final_url},{content_type},{nbytes},{out_path}")
        except urllib.error.HTTPError as exc:
            print(f"HTTP_ERROR,{slug},{url},{exc.code},{exc.reason}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR,{slug},{url},{type(exc).__name__},{exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
