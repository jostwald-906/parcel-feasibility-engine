#!/usr/bin/env python3
"""
Automated RHNA Data Update Script

This script downloads the latest SB35 determination data from the California
Open Data Portal and updates the local cache.

Usage:
    python scripts/update_rhna_data.py

Schedule with cron (weekly on Sundays at 2am):
    0 2 * * 0 cd /path/to/project && python scripts/update_rhna_data.py >> logs/rhna_update.log 2>&1
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging
import urllib.request
import shutil
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data source configuration
SB35_DATA_URL = "https://data.ca.gov/dataset/bfa37117-b20a-4675-a2c5-8ab353668ba8/resource/348134ad-a8fb-4c1a-b22a-c896d45667af/download/sb-35-determination-data.csv"
CKAN_API_BASE = "https://data.ca.gov/api/3/action"
PACKAGE_ID = "sb-35-data"
RESOURCE_ID = "348134ad-a8fb-4c1a-b22a-c896d45667af"

# Local paths
DATA_DIR = project_root / "data"
CSV_FILE = DATA_DIR / "sb35_determinations.csv"
BACKUP_FILE = DATA_DIR / "sb35_determinations.csv.backup"
METADATA_FILE = DATA_DIR / "rhna_metadata.txt"


def check_for_updates() -> dict:
    """
    Check if new data is available via CKAN API.

    Returns:
        Dictionary with update information
    """
    try:
        import json
        api_url = f"{CKAN_API_BASE}/resource_show?id={RESOURCE_ID}"

        logger.info(f"Checking for updates via CKAN API: {api_url}")

        with urllib.request.urlopen(api_url, timeout=30) as response:
            data = json.loads(response.read().decode())

            if data.get('success'):
                resource = data['result']
                return {
                    'available': True,
                    'url': resource.get('url', SB35_DATA_URL),
                    'last_modified': resource.get('last_modified', 'Unknown'),
                    'format': resource.get('format', 'CSV'),
                    'name': resource.get('name', 'SB35 Determination Data')
                }
            else:
                logger.warning("CKAN API returned unsuccessful response")
                return {'available': False}

    except Exception as e:
        logger.warning(f"Could not check for updates via API: {e}")
        logger.info("Will proceed with direct download from known URL")
        return {
            'available': True,
            'url': SB35_DATA_URL,
            'last_modified': 'Unknown',
            'format': 'CSV',
            'name': 'SB35 Determination Data'
        }


def calculate_file_hash(filepath: Path) -> str:
    """
    Calculate MD5 hash of file.

    Args:
        filepath: Path to file

    Returns:
        Hexadecimal hash string
    """
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def download_data(url: str, destination: Path) -> bool:
    """
    Download RHNA data from URL.

    Args:
        url: Download URL
        destination: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading data from: {url}")
        logger.info(f"Destination: {destination}")

        # Create temporary download file
        temp_file = destination.parent / f"{destination.name}.temp"

        # Download with redirect following
        with urllib.request.urlopen(url, timeout=60) as response:
            with open(temp_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        # Verify download (basic check)
        if temp_file.stat().st_size == 0:
            logger.error("Downloaded file is empty")
            temp_file.unlink()
            return False

        # Check if it's actually CSV (starts with valid header)
        with open(temp_file, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            if 'County' not in first_line and 'Jurisdiction' not in first_line:
                logger.error(f"Downloaded file doesn't appear to be valid CSV. First line: {first_line[:100]}")
                temp_file.unlink()
                return False

        # Move temp file to destination
        if destination.exists():
            # Backup existing file
            shutil.copy2(destination, BACKUP_FILE)
            logger.info(f"Backed up existing file to: {BACKUP_FILE}")

        shutil.move(str(temp_file), str(destination))
        logger.info(f"Successfully downloaded data to: {destination}")

        return True

    except Exception as e:
        logger.error(f"Failed to download data: {e}")
        return False


def validate_data(filepath: Path) -> bool:
    """
    Validate downloaded CSV data.

    Args:
        filepath: Path to CSV file

    Returns:
        True if valid, False otherwise
    """
    try:
        import csv

        logger.info(f"Validating data: {filepath}")

        # Required columns
        required_cols = ['County', 'Jurisdiction', '10%', '50%', 'Exempt']

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Check headers
            headers = reader.fieldnames
            missing = [col for col in required_cols if col not in headers]
            if missing:
                logger.error(f"Missing required columns: {missing}")
                return False

            # Count rows
            row_count = sum(1 for _ in reader)
            logger.info(f"Data contains {row_count} jurisdictions")

            if row_count < 100:
                logger.warning(f"Only {row_count} rows found - expected 400+")
                logger.warning("Data may be incomplete")
                return False

        logger.info("Data validation passed")
        return True

    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        return False


def save_metadata(info: dict):
    """
    Save metadata about the update.

    Args:
        info: Update information dictionary
    """
    try:
        with open(METADATA_FILE, 'w') as f:
            f.write(f"RHNA Data Update Metadata\n")
            f.write(f"==========================\n\n")
            f.write(f"Last Updated: {datetime.now().isoformat()}\n")
            f.write(f"Source: {info.get('url', 'Unknown')}\n")
            f.write(f"HCD Last Modified: {info.get('last_modified', 'Unknown')}\n")
            f.write(f"Format: {info.get('format', 'Unknown')}\n")
            f.write(f"File Hash: {info.get('file_hash', 'Unknown')}\n")
            f.write(f"\n")
            f.write(f"Data Source: California HCD SB35 Determination Dataset\n")
            f.write(f"Dataset URL: https://data.ca.gov/dataset/sb-35-data\n")

        logger.info(f"Saved metadata to: {METADATA_FILE}")

    except Exception as e:
        logger.warning(f"Could not save metadata: {e}")


def main():
    """Main update process."""
    logger.info("=" * 60)
    logger.info("RHNA Data Update Process Started")
    logger.info("=" * 60)

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # Check for updates
    update_info = check_for_updates()

    if not update_info.get('available'):
        logger.error("No update information available")
        return 1

    # Check if we already have this version
    if CSV_FILE.exists() and METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r') as f:
                content = f.read()
                if update_info.get('last_modified', '') in content:
                    logger.info("Data is already up to date")
                    logger.info(f"Last modified: {update_info.get('last_modified')}")
                    return 0
        except Exception:
            pass  # Continue with update if we can't read metadata

    # Download new data
    download_url = update_info.get('url', SB35_DATA_URL)
    success = download_data(download_url, CSV_FILE)

    if not success:
        logger.error("Download failed")
        # Restore from backup if available
        if BACKUP_FILE.exists():
            logger.info("Restoring from backup")
            shutil.copy2(BACKUP_FILE, CSV_FILE)
        return 1

    # Validate data
    if not validate_data(CSV_FILE):
        logger.error("Data validation failed")
        # Restore from backup if available
        if BACKUP_FILE.exists():
            logger.info("Restoring from backup due to validation failure")
            shutil.copy2(BACKUP_FILE, CSV_FILE)
        return 1

    # Calculate file hash
    file_hash = calculate_file_hash(CSV_FILE)
    update_info['file_hash'] = file_hash

    # Save metadata
    save_metadata(update_info)

    # Success
    logger.info("=" * 60)
    logger.info("RHNA Data Update Completed Successfully")
    logger.info(f"File: {CSV_FILE}")
    logger.info(f"Size: {CSV_FILE.stat().st_size:,} bytes")
    logger.info(f"Hash: {file_hash}")
    logger.info("=" * 60)

    # Reload service (if running in application context)
    try:
        from app.services.rhna_service import rhna_service
        rhna_service._load_data()
        logger.info("Reloaded RHNA service with new data")

        # Print summary stats
        stats = rhna_service.get_summary_stats()
        logger.info(f"Total jurisdictions: {stats['total_jurisdictions']}")
        logger.info(f"Exempt (met targets): {stats['exempt_count']}")
        logger.info(f"Requires 10% affordable: {stats['requires_10_pct_count']}")
        logger.info(f"Requires 50% affordable: {stats['requires_50_pct_count']}")

    except Exception as e:
        logger.warning(f"Could not reload service: {e}")
        logger.info("Service will reload automatically on next import")

    return 0


if __name__ == "__main__":
    sys.exit(main())
