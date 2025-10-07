"""
California Construction Cost Index (CCCI) client.

NOTE: CCCI is a calculated average of ENR Building Cost Index for Los Angeles
and San Francisco. This is NOT an official government API, but rather data
compiled from ENR (Engineering News-Record) indices.

The CCCI is useful for tracking construction cost inflation in California
over time. Data is typically sourced from CSV files or web scraping.

Sources:
- ENR Building Cost Index (subscription required)
- Historical CCCI compilations
- California state construction cost tracking
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.utils.logging import get_logger

logger = get_logger(__name__)


class CCCIClientError(Exception):
    """Base exception for CCCI client errors."""
    pass


class CCCIClient:
    """
    Client for California Construction Cost Index data.

    Reads CCCI data from CSV files in data/ccci/ directory.
    Data source is marked as 'file' or 'scrape' depending on origin.

    NOTE: CCCI is calculated as the average of ENR-BCI for LA and SF,
    not an official government index.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize CCCI client.

        Args:
            data_dir: Directory containing CCCI CSV files
                     (defaults to project_root/data/ccci/)
        """
        if data_dir is None:
            # Get project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "ccci"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "CCCI client initialized",
            extra={
                "data_dir": str(self.data_dir),
                "note": "CCCI is LA+SF ENR-BCI average, not official API"
            }
        )

    def _find_latest_ccci_file(self) -> Optional[Path]:
        """
        Find the most recent CCCI data file.

        Returns:
            Path to the latest CCCI CSV file, or None if not found
        """
        # Look for CSV files in data directory
        csv_files = list(self.data_dir.glob("ccci_*.csv"))

        if not csv_files:
            logger.warning(
                "No CCCI data files found",
                extra={"data_dir": str(self.data_dir)}
            )
            return None

        # Sort by modification time, most recent first
        latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)

        logger.debug(
            "Found latest CCCI file",
            extra={"file": str(latest_file)}
        )

        return latest_file

    def load_latest_ccci(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent CCCI index value.

        Returns:
            Dictionary with CCCI data:
            {
                "index": float,
                "year": int,
                "quarter": Optional[str],
                "month": Optional[str],
                "as_of_date": str,
                "source": "file" or "scrape",
                "file_path": str,
                "note": "CCCI is LA+SF ENR-BCI average"
            }

            Returns None if no CCCI data file exists.

        Raises:
            CCCIClientError: If file exists but cannot be parsed
        """
        ccci_file = self._find_latest_ccci_file()

        if ccci_file is None:
            logger.info("No CCCI data available - file not found")
            return None

        try:
            # Read CSV file
            with open(ccci_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                raise CCCIClientError(f"CCCI file is empty: {ccci_file}")

            # Get the most recent row (assume sorted by date)
            latest_row = rows[-1]

            # Parse the data (adjust field names based on actual CSV structure)
            result = {
                "index": float(latest_row.get("index", latest_row.get("ccci", 0))),
                "year": int(latest_row.get("year", 0)),
                "quarter": latest_row.get("quarter"),
                "month": latest_row.get("month"),
                "as_of_date": latest_row.get("date", latest_row.get("as_of_date")),
                "source": latest_row.get("source", "file"),
                "file_path": str(ccci_file),
                "note": "CCCI is LA+SF ENR-BCI average, not official government index"
            }

            logger.info(
                "Loaded latest CCCI data",
                extra={
                    "index": result["index"],
                    "year": result["year"],
                    "source": result["source"]
                }
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to load CCCI data: {e}",
                extra={"file": str(ccci_file)}
            )
            raise CCCIClientError(f"Failed to load CCCI data from {ccci_file}: {e}")

    def load_ccci_history(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load full CCCI historical data.

        Returns:
            List of dictionaries with CCCI data over time,
            or None if no data file exists.

        Raises:
            CCCIClientError: If file exists but cannot be parsed
        """
        ccci_file = self._find_latest_ccci_file()

        if ccci_file is None:
            logger.info("No CCCI data available - file not found")
            return None

        try:
            history = []

            with open(ccci_file, "r") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    data_point = {
                        "index": float(row.get("index", row.get("ccci", 0))),
                        "year": int(row.get("year", 0)),
                        "quarter": row.get("quarter"),
                        "month": row.get("month"),
                        "as_of_date": row.get("date", row.get("as_of_date")),
                        "source": row.get("source", "file")
                    }
                    history.append(data_point)

            logger.info(
                "Loaded CCCI history",
                extra={
                    "records": len(history),
                    "file": str(ccci_file)
                }
            )

            return history

        except Exception as e:
            logger.error(
                f"Failed to load CCCI history: {e}",
                extra={"file": str(ccci_file)}
            )
            raise CCCIClientError(
                f"Failed to load CCCI history from {ccci_file}: {e}"
            )

    def calculate_inflation_factor(
        self,
        base_year: int,
        target_year: int
    ) -> Optional[float]:
        """
        Calculate inflation factor between two years using CCCI.

        Args:
            base_year: Starting year
            target_year: Ending year

        Returns:
            Inflation factor (e.g., 1.15 = 15% increase),
            or None if data not available

        Raises:
            CCCIClientError: If calculation fails
        """
        history = self.load_ccci_history()

        if history is None:
            return None

        # Find index values for base and target years
        base_index = None
        target_index = None

        for record in history:
            if record["year"] == base_year and base_index is None:
                base_index = record["index"]
            if record["year"] == target_year:
                target_index = record["index"]

        if base_index is None or target_index is None:
            raise CCCIClientError(
                f"CCCI data not available for years {base_year} to {target_year}"
            )

        inflation_factor = target_index / base_index

        logger.info(
            "Calculated CCCI inflation factor",
            extra={
                "base_year": base_year,
                "target_year": target_year,
                "base_index": base_index,
                "target_index": target_index,
                "inflation_factor": inflation_factor
            }
        )

        return inflation_factor

    def get_data_source_info(self) -> Dict[str, Any]:
        """
        Get information about the CCCI data source.

        Returns:
            Dictionary with data source information
        """
        ccci_file = self._find_latest_ccci_file()

        if ccci_file is None:
            return {
                "available": False,
                "data_dir": str(self.data_dir),
                "note": "CCCI is LA+SF ENR-BCI average, not official government index"
            }

        return {
            "available": True,
            "file_path": str(ccci_file),
            "data_dir": str(self.data_dir),
            "last_modified": datetime.fromtimestamp(
                ccci_file.stat().st_mtime
            ).isoformat(),
            "source_type": "file",
            "note": "CCCI is LA+SF ENR-BCI average, not official government index"
        }


# Module-level convenience function
_default_client: Optional[CCCIClient] = None


def get_ccci_client(data_dir: Optional[Path] = None) -> CCCIClient:
    """
    Get a singleton CCCI client instance.

    Args:
        data_dir: Optional data directory path

    Returns:
        CCCIClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = CCCIClient(data_dir=data_dir)
    return _default_client
