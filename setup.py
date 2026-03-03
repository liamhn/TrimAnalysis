#!/usr/bin/env python3
"""Setup script for TrimAnalysis project - creates conda environment and downloads Zenodo data."""
import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

DEFAULT_DOI = "10.5281/zenodo.14014166"
DOI_URL_PREFIX = "https://doi.org/"
ZENODO_API_PREFIX = "https://zenodo.org/api/records/"
ENV_NAME = "trimanalysis"
ENV_FILE = "environment.yaml"


def extract_zenodo_numeric_id(value: str) -> str | None:
    """Extract numeric Zenodo ID from DOI or URL."""
    match = re.search(r"zenodo\.(\d+)", value)
    if match:
        return match.group(1)
    return None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup conda environment and download Zenodo dataset files."
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
        help="Re-download files even if checksums match.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--skip-env",
        action="store_true",
        help="Skip conda environment creation and Jupyter kernel setup.",
    )
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip Zenodo data download.",
    )
    return parser.parse_args()


def resolve_record_id(doi: str, timeout: int) -> str:
    """Resolve DOI to Zenodo record ID."""
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
    """Fetch Zenodo record metadata."""
    response = requests.get(f"{ZENODO_API_PREFIX}{record_id}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_latest_version_record(parent_id: str, timeout: int) -> dict | None:
    """Fetch latest version of a Zenodo record by parent ID."""
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


def compute_md5(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute MD5 checksum of a file."""
    md5_hash = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def extract_zip_file(zip_path: Path, extract_to: Path | None = None) -> None:
    """Extract a zip file to the same directory or specified location."""
    if not zip_path.exists():
        return

    extract_dir = extract_to or zip_path.parent
    print(f"Extracting: {zip_path.name}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✓ Extracted to: {extract_dir}")
    except zipfile.BadZipFile:
        print(f"⚠ Warning: {zip_path.name} is not a valid zip file, skipping extraction.")
    except Exception as e:
        print(f"⚠ Warning: Could not extract {zip_path.name}: {e}")


def download_file(url: str, destination: Path, timeout: int) -> None:
    """Download a file with progress bar."""
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


def run_command(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command. Uses shell=True on Windows for better compatibility."""
    # Verify the command exists
    if not shutil.which(cmd[0]):
        raise FileNotFoundError(f"Command not found in PATH: {cmd[0]}")
    
    kwargs = {"check": check}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    
    # On Windows, use shell=True for better conda compatibility
    if platform.system() == "Windows":
        kwargs["shell"] = True
        # Convert list to string for shell execution
        cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)
        return subprocess.run(cmd_str, **kwargs)
    else:
        return subprocess.run(cmd, **kwargs)


def conda_env_exists(env_name: str) -> bool:
    """Check if conda environment exists."""
    try:
        result = run_command(
            ["conda", "env", "list", "--json"],
            capture=True,
        )
        envs_data = json.loads(result.stdout)
        env_paths = envs_data.get("envs", [])
        for env_path in env_paths:
            if env_name in env_path or env_path.endswith(env_name):
                return True
        return False
    except Exception:
        return False


def create_conda_env(env_file: Path) -> None:
    """Create conda environment from YAML file."""
    if not env_file.exists():
        abs_path = env_file.resolve()
        raise FileNotFoundError(
            f"Environment file not found: {env_file}\n"
            f"Looked for: {abs_path}\n"
            f"Current directory: {Path.cwd()}"
        )

    print(f"Creating conda environment '{ENV_NAME}' from {env_file.resolve()}...")
    try:
        # Use shell=True on Windows for better conda integration
        run_command(["conda", "env", "create", "-f", str(env_file.resolve()), "-n", ENV_NAME])
        print(f"✓ Conda environment '{ENV_NAME}' created successfully.")
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Conda command not found. Make sure conda is installed and in your PATH.\n"
            f"Error: {e}"
        )


def install_jupyter_kernel(env_name: str) -> None:
    """Install conda environment as Jupyter kernel."""
    print(f"Registering '{env_name}' as Jupyter kernel...")

    # Install ipykernel in the environment if not present
    run_command(
        ["conda", "run", "-n", env_name, "python", "-m", "pip", "install", "ipykernel"],
        check=False,
    )

    # Register kernel
    run_command(
        [
            "conda", "run", "-n", env_name, "python", "-m", "ipykernel",
            "install", "--user", "--name", env_name,
            "--display-name", f"Python ({env_name})",
        ],
    )
    print(f"✓ Jupyter kernel '{env_name}' registered successfully.")


def setup_conda_environment(skip: bool) -> None:
    """Setup conda environment and Jupyter kernel."""
    if skip:
        print("Skipping conda environment setup (--skip-env flag).")
        return

    env_file = Path(ENV_FILE)
    
    # Check if environment.yaml exists in current directory
    if not env_file.exists():
        # Try to find it in common locations
        search_paths = [
            Path.cwd() / "environment.yaml",
            Path(__file__).parent / "environment.yaml",
        ]
        
        found = False
        for search_path in search_paths:
            if search_path.exists():
                env_file = search_path
                found = True
                break
        
        if not found:
            print(
                f"⚠ Warning: {ENV_FILE} not found.\n"
                f"  Expected in: {Path.cwd() / ENV_FILE}\n"
                f"  Current directory: {Path.cwd()}\n"
                f"  Skipping environment setup. Please ensure environment.yaml is in the same directory as setup.py."
            )
            return
    
    if conda_env_exists(ENV_NAME):
        print(f"✓ Conda environment '{ENV_NAME}' already exists.")
    else:
        create_conda_env(env_file)

    # Always try to register kernel (idempotent operation)
    try:
        install_jupyter_kernel(ENV_NAME)
    except Exception as e:
        print(f"Warning: Could not register Jupyter kernel: {e}")
        print("You can manually register it later with:")
        print(f"  conda activate {ENV_NAME}")
        print(f"  python -m ipykernel install --user --name {ENV_NAME}")


def download_zenodo_data(args: argparse.Namespace) -> None:
    """Download Zenodo dataset files with checksum verification."""
    if args.skip_data:
        print("Skipping Zenodo data download (--skip-data flag).")
        return

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

    # Check if we have existing metadata to compare
    existing_record_id = None
    if metadata_file.exists():
        try:
            existing_metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            existing_record_id = str(existing_metadata.get("id", ""))
        except Exception:
            pass

    if existing_record_id and existing_record_id != str(record_id):
        print(f"New Zenodo version detected (old: {existing_record_id}, new: {record_id})")

    # Save current metadata
    metadata_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

    downloaded = 0
    skipped = 0
    updated = 0

    for file_info in files:
        file_name = file_info.get("key") or file_info.get("filename")
        links = file_info.get("links", {})
        file_url = links.get("self") or links.get("download")
        expected_checksum = file_info.get("checksum", "").replace("md5:", "")

        if not file_name or not file_url:
            continue

        destination = output_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)

        need_download = args.force or not destination.exists()

        # If file exists and we're not forcing, check checksum
        if destination.exists() and not args.force and expected_checksum:
            print(f"Verifying checksum for: {file_name}")
            actual_checksum = compute_md5(destination)
            if actual_checksum == expected_checksum:
                print(f"✓ File up to date: {file_name}")
                skipped += 1
                continue
            else:
                print(f"Checksum mismatch for {file_name}, re-downloading...")
                need_download = True
                updated += 1

        if need_download:
            print(f"Downloading: {file_name}")
            download_file(file_url, destination, args.timeout)

            # Verify downloaded file
            if expected_checksum:
                actual_checksum = compute_md5(destination)
                if actual_checksum == expected_checksum:
                    print(f"✓ Checksum verified for: {file_name}")
                else:
                    print(f"⚠ Warning: Checksum mismatch for {file_name}")

            downloaded += 1

        # Extract zip files after download/verification
        if destination.suffix.lower() == ".zip":
            extract_zip_file(destination)

    summary_parts = []
    if downloaded:
        summary_parts.append(f"downloaded {downloaded} file(s)")
    if updated:
        summary_parts.append(f"updated {updated} file(s)")
    if skipped:
        summary_parts.append(f"skipped {skipped} up-to-date file(s)")

    print(f"✓ Data sync complete: {', '.join(summary_parts)}.")
    print(f"Metadata saved to {metadata_file}.")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("TrimAnalysis Setup")
    print("=" * 60)

    # Step 1: Setup conda environment
    try:
        setup_conda_environment(args.skip_env)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Continuing with data download...")
    except RuntimeError as e:
        print(f"Error: {e}")
        print(f"Continuing with data download...")
    except Exception as e:
        print(f"Error setting up conda environment: {e}")
        print(f"Continuing with data download...")

    print()

    # Step 2: Download/update Zenodo data
    try:
        download_zenodo_data(args)
    except Exception as e:
        print(f"Error downloading Zenodo data: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    if not args.skip_env:
        print(f"To activate the environment: conda activate {ENV_NAME}")
        print(f"To launch Jupyter: jupyter lab")
    print(f"Data location: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
