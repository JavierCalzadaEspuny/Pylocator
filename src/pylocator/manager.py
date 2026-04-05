"""GeoNames download and cache manager for country-level geolocation data."""

import pickle
from pathlib import Path
from typing import Callable
from urllib.request import urlopen

from .models import DEFAULT_CACHE, GEONAMES_URL


class GeoDataManager:
    """
    Manages persistent cache storage and on-demand download of GeoNames country datasets.

    Methods
    -------
    get_country_data(self, code, parser): Return cached or freshly parsed data for a country.

    Example
    -------
    >>> mgr = GeoDataManager()
    >>> data = mgr.get_country_data("LB", parser)
    """

    def __init__(self, cache_path: str | Path | None = None):
        """
        Initialize the cache manager and ensure the cache directory exists.

        Parameters
        ----------
        cache_path : str | Path | None
            Optional directory where processed country cache files are stored.

        Returns
        -------
        None
            This constructor configures the manager in place.
        """
        self.path = Path(cache_path) if cache_path else DEFAULT_CACHE
        self.path.mkdir(parents=True, exist_ok=True)

    def get_country_data(self, code: str, parser: Callable[[bytes, str], dict]):
        """
        Return geolocation data for a country using cache-first loading.

        Parameters
        ----------
        code : str
            Country code used to resolve the GeoNames country dump.
        parser : Callable[[bytes, str], dict]
            Function that converts downloaded ZIP bytes into an in-memory index.

        Returns
        -------
        dict
            Parsed country data loaded from cache or from a fresh download.
        """
        country = code.upper()
        pkl_path = self.path / f"{country}.pkl"

        if pkl_path.exists():
            try:
                with open(pkl_path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                pkl_path.unlink(missing_ok=True)

        with urlopen(GEONAMES_URL.format(country), timeout=30) as r:
            data = parser(r.read(), country)

        with open(pkl_path, "wb") as f:
            pickle.dump(data, f)

        return data


if __name__ == "__main__":
    mgr = GeoDataManager()
    print("Geo manager OK")
    print(f"Cache dir: {mgr.path}")
