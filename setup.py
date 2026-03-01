#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import requests
from tqdm import tqdm

DEFAULT_DOI = "10.5281/zenodo.14014166"
DOI_URL_PREFIX = "https://doi.org/"
ZENODO_API_PREFIX = "https://zenodo.org/api/records/"


def extract_zenodo_numeric_id(value: str) -> str | None:
    match = re.search(r"zenodo\.(\d+)", value)
    if match:
        return match.group(1)
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Zenodo dataset files for this repository."
    )
    parser.add_argument(
        "--doi",
        default=DEFAULT_DOI,
        help=f"DOI to download (default: {DEFAULT_DOI})",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory where downloaded files are stored (default: data)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60)",
    )
    return parser.parse_args()


def resolve_record_id(doi: str, timeout: int) -> str:
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    response = requests.get(f"{DOI_URL_PREFIX}{doi}", allow_redirects=True, timeout=timeout)
    response.raise_for_status()
    final_url = response.url

    match = re.search(r"/records/(\d+)", final_url)
    if match:
        return match.group(1)

    fallback_id = extract_zenodo_numeric_id(doi)
    if fallback_id:
        return fallback_id

    raise RuntimeError(f"Could not resolve Zenodo record ID from URL: {final_url}")


def fetch_record(record_id: str, timeout: int) -> dict:
    response = requests.get(f"{ZENODO_API_PREFIX}{record_id}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_latest_version_record(parent_id: str, timeout: int) -> dict | None:
    response = requests.get(
        "https://zenodo.org/api/records",
        params={"q": f"parent.id:{parent_id}", "sort": "newest", "size": 1},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    hits = payload.get("hits", {}).get("hits", [])
    if not hits:
        return None
    return hits[0]


def download_file(url: str, destination: Path, timeout: int) -> None:
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))

        with destination.open("wb") as file_handle:
            with tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=destination.name,
            ) as progress:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    file_handle.write(chunk)
                    progress.update(len(chunk))


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    record_id = resolve_record_id(args.doi, args.timeout)
    print(f"Resolved DOI to Zenodo record: {record_id}")

    record = fetch_record(record_id, args.timeout)
    files = record.get("files", [])

    if not files:
        latest_record = fetch_latest_version_record(record_id, args.timeout)
        if latest_record:
            latest_files = latest_record.get("files", [])
            if latest_files:
                record = latest_record
                files = latest_files
                record_id = str(record.get("id", record_id))
                print(f"Using latest versioned record: {record_id}")

    if not files:
        raise RuntimeError("No files found on Zenodo record.")

    metadata_file = output_dir / "zenodo_record.json"
    metadata_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

    downloaded = 0
    skipped = 0

    for file_info in files:
        file_name = file_info.get("key") or file_info.get("filename")
        links = file_info.get("links", {})
        file_url = links.get("self") or links.get("download")

        if not file_name or not file_url:
            continue

        destination = output_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and not args.force:
            print(f"Skipping existing file: {destination}")
            skipped += 1
            continue

        print(f"Downloading: {file_name}")
        download_file(file_url, destination, args.timeout)
        downloaded += 1

    print(
        f"Done. Downloaded {downloaded} file(s), skipped {skipped} existing file(s). "
        f"Metadata saved to {metadata_file}."
    )


if __name__ == "__main__":
    main()
