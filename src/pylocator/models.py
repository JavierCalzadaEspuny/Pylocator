"""Shared models, constants, and regex patterns for geolocation processing."""


import os
import re
from pathlib import Path
from typing import NamedTuple

PROJECT_NAME = "pylocator"

# ==============================
# Constants
# ==============================
GEONAMES_URL = "https://download.geonames.org/export/dump/{}.zip"

# ==============================
# Cache Paths
# ==============================

def _default_cache_dir() -> Path:
    """Build and create the default geolocator cache directory in home."""
    path = Path.home() / f".cache_{PROJECT_NAME}"
    path.mkdir(parents=True, exist_ok=True)
    return path


DEFAULT_CACHE = _default_cache_dir()

ARABIC_FALLBACK = {
    "ى": "ي",
    "ة": "ه",
}

PUNCT_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)
TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


# ==============================
# Data Models
# ==============================

class Place(NamedTuple):
    """
    Immutable place record used by the geolocation engine and client.

    Methods
    -------
    _asdict(self): Return the record as a dictionary.
    _replace(self, **kwargs): Return a new record with selected fields replaced.

    Example
    -------
    >>> p = Place(1, "Beirut", 33.89, 35.50, 1900000, "LB", "P", "PPLC", "04", 0)
    >>> p.name
    'Beirut'
    """

    geonameid: int
    name: str
    lat: float
    lon: float
    population: int
    country: str
    feature_class: str
    feature_type: str
    admin_code: str
    elevation: int


if __name__ == "__main__":
    print("Geo models OK")
    print(f"Default cache: {DEFAULT_CACHE}")
