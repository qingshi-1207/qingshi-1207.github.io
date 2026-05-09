"""
从 OpenAlex 拉取作者论文列表，并过滤预印本/仓库条目。

默认输出字段兼容现有 auto-pub-list.json 的结构：
{
  "last_updated": "...",
  "source": "OpenAlex",
  "total_count": N,
  "publications": [
    {
      "id": "...",
      "title": "...",
      "authors": ["..."],
      "venue": "...",
      "year": "2025",
      "link": "...",
      "type": "Journal|Conference|Unknown",
      "doi": "..."
    }
  ]
}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

OPENALEX_API = "https://api.openalex.org"
CROSSREF_API = "https://api.crossref.org/works"
DEFAULT_AUTHOR_NAME = "Mingming Fan"
DEFAULT_OUTPUT_FILE = "assets/data/auto-pub-list-openalex.json"
REQUEST_TIMEOUT = 20
PREPRINT_KEYWORDS = ("arxiv", "corr", "preprint", "biorxiv", "medrxiv", "ssrn")


def request_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {
        "User-Agent": "APEX-Web-publication-sync/1.0 (mailto:example@example.com)"
    }
    query = urlencode(params or {})
    full_url = f"{url}?{query}" if query else url
    req = Request(full_url, headers=headers)
    with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:  # nosec B310
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    lower = doi.lower()
    if lower.startswith("https://doi.org/"):
        return doi[16:]
    if lower.startswith("http://doi.org/"):
        return doi[15:]
    if lower.startswith("doi.org/"):
        return doi[8:]
    return doi


def fetch_crossref_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_doi(doi)
    if not normalized:
        return None
    url = f"{CROSSREF_API}/{quote(normalized, safe='')}"
    try:
        payload = request_json(url)
    except Exception:
        return None
    return payload.get("message") if isinstance(payload, dict) else None


def extract_crossref_authors(message: Dict[str, Any]) -> List[str]:
    authors = []
    for a in message.get("author", []) or []:
        name = (a.get("name") or "").strip()
        if not name:
            given = (a.get("given") or "").strip()
            family = (a.get("family") or "").strip()
            name = f"{given} {family}".strip()
        if name:
            authors.append(name)
    return authors


def extract_crossref_venue(message: Dict[str, Any]) -> str:
    container = message.get("container-title") or []
    if container and isinstance(container, list) and container[0]:
        return str(container[0]).strip()
    short_container = message.get("short-container-title") or []
    if short_container and isinstance(short_container, list) and short_container[0]:
        return str(short_container[0]).strip()
    return ""


def infer_type_from_crossref(message: Dict[str, Any]) -> str:
    # Crossref type 参考: journal-article / proceedings-article / posted-content ...
    raw_type = (message.get("type") or "").strip().lower()
    if raw_type in {"journal-article", "journal", "journal-volume", "journal-issue"}:
        return "Journal"
    if raw_type in {
        "proceedings-article",
        "proceedings",
        "book-chapter",
        "reference-entry",
    }:
        return "Conference"

    container = " ".join(message.get("container-title") or []).lower()
    if any(k in container for k in ["proceedings", "conference", "symposium", "workshop"]):
        return "Conference"
    if any(
        k in container
        for k in ["journal", "transactions", "letters", "review", "interacting with computers"]
    ):
        return "Journal"
    return "Unknown"


def print_progress(current: int, total: int, prefix: str = "") -> None:
    if total <= 0:
        return
    width = 30
    ratio = current / total
    done = int(width * ratio)
    bar = "=" * done + "." * (width - done)
    print(f"\r{prefix} [{bar}] {current}/{total} ({ratio * 100:5.1f}%)", end="", flush=True)
    if current >= total:
        print()


def backfill_from_crossref(
    publications: List[Dict[str, Any]],
    reprocess: bool = False,
) -> Dict[str, int]:
    cache: Dict[str, Optional[Dict[str, Any]]] = {}
    need_backfill = [
        pub
        for pub in publications
        if reprocess or not pub.get("backfill_processed", False)
    ]
    print(f"[INFO] Crossref backfill candidates: {len(need_backfill)}")

    stats = {
        "candidates": len(need_backfill),
        "updated_venue": 0,
        "updated_authors": 0,
        "updated_type": 0,
        "skipped_no_doi": 0,
        "not_found": 0,
        "processed": 0,
    }

    for idx, pub in enumerate(need_backfill, start=1):
        doi = normalize_doi(pub.get("doi", ""))
        if not doi:
            pub["backfill_processed"] = True
            pub["backfill_source"] = "crossref"
            pub["backfill_status"] = "skipped_no_doi"
            pub["backfill_updated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats["skipped_no_doi"] += 1
            stats["processed"] += 1
            print_progress(idx, len(need_backfill), prefix="[Backfill]")
            continue
        if doi not in cache:
            cache[doi] = fetch_crossref_by_doi(doi)
        message = cache[doi]
        if not message:
            pub["backfill_processed"] = True
            pub["backfill_source"] = "crossref"
            pub["backfill_status"] = "not_found"
            pub["backfill_updated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats["not_found"] += 1
            stats["processed"] += 1
            print_progress(idx, len(need_backfill), prefix="[Backfill]")
            continue

        if not (pub.get("venue") or "").strip():
            venue = extract_crossref_venue(message)
            if venue:
                pub["venue"] = venue
                stats["updated_venue"] += 1

        authors = extract_crossref_authors(message)
        if authors:
            pub["authors"] = authors
            stats["updated_authors"] += 1

        inferred_type = infer_type_from_crossref(message)
        old_type = (pub.get("type") or "Unknown").strip()
        if old_type not in {"Journal", "Conference"} and inferred_type in {"Journal", "Conference"}:
            pub["type"] = inferred_type
            stats["updated_type"] += 1

        pub["backfill_processed"] = True
        pub["backfill_source"] = "crossref"
        pub["backfill_status"] = "ok"
        pub["backfill_updated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats["processed"] += 1
        print_progress(idx, len(need_backfill), prefix="[Backfill]")

    return stats


def find_author_id(author_name: str) -> Optional[str]:
    data = request_json(
        f"{OPENALEX_API}/authors",
        {"search": author_name, "per-page": 10},
    )
    results = data.get("results", [])
    if not results:
        return None

    target = author_name.strip().lower()
    for author in results:
        name = (author.get("display_name") or "").strip().lower()
        if name == target:
            return author.get("id")

    return results[0].get("id")


def looks_like_preprint_or_repository(work: Dict[str, Any]) -> bool:
    work_type = (work.get("type") or "").lower()
    if work_type == "preprint":
        return True

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    source_type = (source.get("type") or "").lower()
    source_name = (source.get("display_name") or "").lower()

    if source_type == "repository":
        return True
    return any(k in source_name for k in PREPRINT_KEYWORDS)


def infer_entry_type(work: Dict[str, Any]) -> str:
    source = ((work.get("primary_location") or {}).get("source") or {})
    source_type = (source.get("type") or "").lower()
    if source_type == "journal":
        return "Journal"
    if source_type == "conference":
        return "Conference"
    return "Unknown"


def normalize_work(work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if looks_like_preprint_or_repository(work):
        return None

    title = (work.get("display_name") or "").strip()
    year = work.get("publication_year")
    if not title or not year:
        return None

    authorships = work.get("authorships") or []
    authors = []
    for a in authorships:
        author_name = ((a.get("author") or {}).get("display_name") or "").strip()
        if author_name:
            authors.append(author_name)

    source = ((work.get("primary_location") or {}).get("source") or {})
    venue = (source.get("display_name") or "").strip()

    link = (work.get("primary_location") or {}).get("landing_page_url") or work.get("id") or ""
    doi = work.get("doi") or ""
    openalex_id = work.get("id") or ""

    return {
        "id": openalex_id,
        "title": title,
        "authors": authors,
        "venue": venue,
        "year": str(year),
        "link": link,
        "type": infer_entry_type(work),
        "doi": doi,
    }


def fetch_all_works(author_id: str, max_items: int = 500) -> List[Dict[str, Any]]:
    works: List[Dict[str, Any]] = []
    cursor = "*"

    while True:
        params = {
            "filter": f"authorships.author.id:{author_id}",
            "per-page": 200,
            "cursor": cursor,
            "sort": "publication_year:desc",
        }
        data = request_json(f"{OPENALEX_API}/works", params)
        batch = data.get("results", [])
        works.extend(batch)

        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")
        if not next_cursor or len(works) >= max_items:
            break
        cursor = next_cursor

    return works[:max_items]


def dedupe_publications(publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []
    for pub in publications:
        key = (pub.get("doi") or "").lower().strip()
        if not key:
            key = f'{pub.get("title", "").lower().strip()}::{pub.get("year", "").strip()}'
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pub)
    return deduped


def publication_key(pub: Dict[str, Any]) -> str:
    doi_key = normalize_doi(pub.get("doi", "")).lower().strip()
    if doi_key:
        return f"doi::{doi_key}"
    openalex_id = (pub.get("id") or "").strip().lower()
    if openalex_id:
        return f"id::{openalex_id}"
    return f'ty::{pub.get("title", "").strip().lower()}::{str(pub.get("year", "")).strip()}'


def load_existing_output(output_file: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    output_path = Path(output_file)
    if not output_path.exists():
        return [], {}
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception:
        return [], {}
    pubs = data.get("publications") or []
    if not isinstance(pubs, list):
        pubs = []
    return pubs, data


def merge_incremental(
    existing_pubs: List[Dict[str, Any]],
    fetched_pubs: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    merged = list(existing_pubs)
    existing_keys = {publication_key(p) for p in existing_pubs}
    added = 0
    for pub in fetched_pubs:
        k = publication_key(pub)
        if k in existing_keys:
            continue
        merged.append(pub)
        existing_keys.add(k)
        added += 1
    return merged, added


def save_json(publications: List[Dict[str, Any]], output_file: str) -> None:
    output = {
        "last_updated": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "OpenAlex",
        "total_count": len(publications),
        "publications": publications,
    }
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch publications from OpenAlex.")
    parser.add_argument(
        "--author-name",
        default=DEFAULT_AUTHOR_NAME,
        help="Author display name for OpenAlex author search.",
    )
    parser.add_argument(
        "--author-id",
        default="",
        help="OpenAlex author id, e.g. https://openalex.org/A1234567890",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=500,
        help="Maximum works to fetch before filtering/dedup.",
    )
    parser.add_argument(
        "--reprocess-backfill",
        action="store_true",
        help="Reprocess backfill for all existing publications.",
    )
    args = parser.parse_args()

    author_id = args.author_id.strip() or find_author_id(args.author_name)
    if not author_id:
        print(f"[ERROR] Cannot find OpenAlex author for name: {args.author_name}")
        return 1

    print(f"[INFO] Using author id: {author_id}")
    works = fetch_all_works(author_id, max_items=args.max_items)
    normalized = []
    for work in works:
        item = normalize_work(work)
        if item:
            normalized.append(item)
    normalized = dedupe_publications(normalized)

    existing_pubs, _ = load_existing_output(args.output)
    merged, added_count = merge_incremental(existing_pubs, normalized)
    print(
        f"[INFO] Existing: {len(existing_pubs)}, fetched: {len(normalized)}, added new: {added_count}"
    )

    backfill_stats = backfill_from_crossref(
        merged,
        reprocess=args.reprocess_backfill,
    )

    merged.sort(
        key=lambda x: (
            int(x.get("year", "0") or 0),
            x.get("title", "").lower(),
        ),
        reverse=True,
    )

    save_json(merged, args.output)
    print(
        "[INFO] Backfill stats: "
        f"processed={backfill_stats['processed']}, "
        f"authors_updated={backfill_stats['updated_authors']}, "
        f"venue_updated={backfill_stats['updated_venue']}, "
        f"type_updated={backfill_stats['updated_type']}, "
        f"no_doi={backfill_stats['skipped_no_doi']}, "
        f"not_found={backfill_stats['not_found']}"
    )
    print(f"[INFO] Saved {len(merged)} publications -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
