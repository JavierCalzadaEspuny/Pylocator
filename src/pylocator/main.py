"""High-level geolocation client with country data management and search helpers."""

import asyncio
import io
import zipfile
from typing import Any, Dict, List, Optional

from pylocator.engine import GeoEngine
from pylocator.manager import GeoDataManager
from pylocator.models import Place


class Geolocator:
    """
    Singleton geolocation client for loading country data and resolving place names.

    Build the object first, then load countries explicitly with add_countries().
    Every call to Geolocator() returns the same shared instance.

    Example
    -------
    >>> geo = Geolocator()
    >>> geo.add_countries(["LB", "SY"])
    >>> results = geo.locate_in(query="Beirut", only=["LB", "SY"], fuzzy=True, threshold=85, limit=3)
    >>> results[0]
    {'geonameid': 170166, 'name': 'Beirut', 'lat': 33.88894, 'lon': 35.49442, 'population': 361366, 'country': 'LB', 'feature_class': 'P', 'feature_type': 'PPLC', 'admin_code': '16', 'elevation': 0, 'score': 100.0}
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Return a shared instance so Geolocator behaves as a singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
    ):
        if getattr(self, "_initialized", False):
            return

        self.manager = GeoDataManager()
        self.engine = GeoEngine()

        self.country_indexes: Dict[str, Dict[str, List[Place]]] = {}
        self.search_index: Dict[str, List[Place]] = {}
        self.active_countries = set()
        self._initialized = True

    def _add_key(self, country_data: Dict[str, List[Place]], raw_key: str, rec: Place) -> None:
        """Insert a normalized key into a country index while avoiding duplicate records."""
        key = self.engine.normalize(raw_key)
        if len(key) < 2:
            return

        bucket = country_data.setdefault(key, [])
        if any(existing.geonameid == rec.geonameid for existing in bucket):
            return
        bucket.append(rec)

    def _parse_zip(self, zip_content: bytes, code: str) -> Dict[str, List[Place]]:
        """Parse a GeoNames ZIP payload into a normalized per-country lookup index."""
        country_data: Dict[str, List[Place]] = {}
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            with zf.open(f"{code}.txt") as f:
                for line in f:
                    cols = line.decode("utf-8", errors="ignore").rstrip("\n").split("\t")
                    if len(cols) < 15:
                        continue

                    geonameid = int(cols[0]) if cols[0].isdigit() else 0
                    pop = int(cols[14]) if cols[14].isdigit() else 0
                    elev = int(cols[15]) if len(cols) > 15 and cols[15].strip().lstrip("-").isdigit() else 0

                    rec = Place(
                        geonameid=geonameid,
                        name=cols[1],
                        lat=float(cols[4]),
                        lon=float(cols[5]),
                        population=pop,
                        country=code,
                        feature_class=cols[6],
                        feature_type=cols[7],
                        admin_code=cols[10],
                        elevation=elev,
                    )

                    self._add_key(country_data, cols[1], rec)
                    if cols[2]:
                        self._add_key(country_data, cols[2], rec)

                    if cols[3]:
                        for alt in cols[3].split(","):
                            alt = alt.strip()
                            if alt:
                                self._add_key(country_data, alt, rec)

        return country_data

    def _rebuild_index(self) -> None:
        """Rebuild the merged search index from all currently active country indexes."""
        merged: Dict[str, List[Place]] = {}

        for code in self.active_countries:
            for key, places in self.country_indexes.get(code, {}).items():
                bucket = merged.setdefault(key, [])
                for place in places:
                    if any(existing.geonameid == place.geonameid for existing in bucket):
                        continue
                    bucket.append(place)

        for key in merged:
            merged[key].sort(key=lambda p: p.population, reverse=True)

        self.search_index = merged

    def _scoped_index(self, only: List[str]) -> Dict[str, List[Place]]:
        """Build and return a temporary merged index limited to specific countries."""
        codes = [c.upper() for c in only if c and c.strip()]
        if not codes:
            return {}

        missing = [c for c in codes if c not in self.active_countries]
        if missing:
            self.add_countries(missing)

        merged: Dict[str, List[Place]] = {}
        for code in codes:
            for key, places in self.country_indexes.get(code, {}).items():
                bucket = merged.setdefault(key, [])
                for place in places:
                    if any(existing.geonameid == place.geonameid for existing in bucket):
                        continue
                    bucket.append(place)

        for key in merged:
            merged[key].sort(key=lambda p: p.population, reverse=True)

        return merged

    def add_countries(self, codes: List[str]) -> None:
        """
        Load, cache, and index one or more country datasets.

        Parameters
        ----------
        codes : List[str]
            Country codes to load and activate in the global search index.

        Returns
        -------
        None
            The client index state is updated in place.
        """
        for code in [c.upper() for c in codes]:
            if code in self.active_countries:
                continue

            try:
                data = self.manager.get_country_data(code, self._parse_zip)
                self.country_indexes[code] = data
                self.active_countries.add(code)
            except Exception as e:
                print(f"Error loading {code}: {e}")

        self._rebuild_index()

    async def aadd_countries(self, codes: List[str]) -> None:
        """
        Asynchronously load and index one or more country datasets.

        Parameters
        ----------
        codes : List[str]
            Country codes to load and activate in the global search index.

        Returns
        -------
        None
            The client index state is updated in place.
        """
        await asyncio.to_thread(self.add_countries, codes)

    def parse_locations(
        self,
        text: str,
        max_ngram: int = 4,
        fuzzy_fallback: bool = True,
    ) -> List[str]:
        """
        Extract location names from sentence text using n-grams and optional fuzzy fallback.

        Parameters
        ----------
        text : str
            Source text that may contain one or more location mentions.
        max_ngram : int
            Maximum n-gram size to scan when looking for place names.
        fuzzy_fallback : bool
            Whether to fall back to fuzzy matching when no exact extraction is found.

        Returns
        -------
        List[str]
            Deduplicated list of resolved location names.
        """
        tokens = self.engine.tokenize(text)
        if not tokens:
            return []

        out: List[str] = []
        used = [False] * len(tokens)

        max_ngram = max(1, max_ngram)
        for i, n, phrase in self.engine.iter_ngrams(tokens, max_ngram):
            if any(used[j] for j in range(i, i + n)):
                continue

            norm = self.engine.normalize(phrase)
            candidates = self.search_index.get(norm)
            if not candidates:
                continue

            out.append(candidates[0].name)
            for j in range(i, i + n):
                used[j] = True

        if not out and fuzzy_fallback:
            fuzzy = self.locate(text, fuzzy=True, fuzzy_threshold=90, max_results=10)
            out = [item["name"] for item in fuzzy]

        return list(dict.fromkeys(out))

    async def aparse_locations(
        self,
        text: str,
        max_ngram: int = 4,
        fuzzy_fallback: bool = True,
    ) -> List[str]:
        """
        Asynchronously extract location names from sentence text.

        Parameters
        ----------
        text : str
            Source text that may contain one or more location mentions.
        max_ngram : int
            Maximum n-gram size to scan when looking for place names.
        fuzzy_fallback : bool
            Whether to fall back to fuzzy matching when no exact extraction is found.

        Returns
        -------
        List[str]
            Deduplicated list of resolved location names.
        """
        return await asyncio.to_thread(self.parse_locations, text, max_ngram, fuzzy_fallback)

    def locate(
        self,
        place_name: str,
        fuzzy: bool = False,
        fuzzy_threshold: int = 90,
        max_results: int = 10,
        preferred_countries: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Resolve a place query against all active countries.

        Parameters
        ----------
        place_name : str
            Input place query to resolve.
        fuzzy : bool
            Whether fuzzy matching is allowed when exact matching fails.
        fuzzy_threshold : int
            Minimum fuzzy score required for candidate acceptance.
        max_results : int
            Maximum number of matches to return.
        preferred_countries : Optional[List[str]]
            Optional country preference order for ranking.

        Returns
        -------
        List[Dict[str, Any]]
            Ranked match list with location metadata and matching score.
        """
        return self.engine.locate(
            q=place_name,
            idx=self.search_index,
            fz=fuzzy,
            thr=fuzzy_threshold,
            top=max_results,
            pref=preferred_countries,
        )

    def locate_in(
        self,
        query: str,
        only: str | List[str],
        fuzzy: bool = False,
        threshold: int = 90,
        limit: int = 10,
        prefer: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Resolve a place query restricted to a selected set of countries.

        Parameters
        ----------
        query : str
            Input place query to resolve.
        only : str | List[str]
            One country code or a list of country codes defining the search scope.
        fuzzy : bool
            Whether fuzzy matching is allowed when exact matching fails.
        threshold : int
            Minimum fuzzy score required for candidate acceptance.
        limit : int
            Maximum number of matches to return.
        prefer : Optional[List[str]]
            Optional country preference order for ranking.

        Returns
        -------
        List[Dict[str, Any]]
            Ranked match list limited to the requested country scope.
        """
        only_codes = [only] if isinstance(only, str) else list(only)
        scoped = self._scoped_index(only_codes)
        pref = prefer if prefer is not None else [c.upper() for c in only_codes]

        return self.engine.locate(
            q=query,
            idx=scoped,
            fz=fuzzy,
            thr=threshold,
            top=limit,
            pref=pref,
        )

    async def alocate(
        self,
        place_name: str,
        fuzzy: bool = True,
        fuzzy_threshold: int = 90,
        max_results: int = 10,
        preferred_countries: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously resolve a place query against all active countries.

        Parameters
        ----------
        place_name : str
            Input place query to resolve.
        fuzzy : bool
            Whether fuzzy matching is allowed when exact matching fails.
        fuzzy_threshold : int
            Minimum fuzzy score required for candidate acceptance.
        max_results : int
            Maximum number of matches to return.
        preferred_countries : Optional[List[str]]
            Optional country preference order for ranking.

        Returns
        -------
        List[Dict[str, Any]]
            Ranked match list with location metadata and matching score.
        """
        return await asyncio.to_thread(
            self.locate,
            place_name,
            fuzzy,
            fuzzy_threshold,
            max_results,
            preferred_countries,
        )

    async def alocate_in(
        self,
        query: str,
        only: str | List[str],
        fuzzy: bool = True,
        threshold: int = 90,
        limit: int = 10,
        prefer: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously resolve a place query within a selected country scope.

        Parameters
        ----------
        query : str
            Input place query to resolve.
        only : str | List[str]
            One country code or a list of country codes defining the search scope.
        fuzzy : bool
            Whether fuzzy matching is allowed when exact matching fails.
        threshold : int
            Minimum fuzzy score required for candidate acceptance.
        limit : int
            Maximum number of matches to return.
        prefer : Optional[List[str]]
            Optional country preference order for ranking.

        Returns
        -------
        List[Dict[str, Any]]
            Ranked match list limited to the requested country scope.
        """
        return await asyncio.to_thread(
            self.locate_in,
            query,
            only,
            fuzzy,
            threshold,
            limit,
            prefer,
        )

    def sentence_locations(
        self,
        text: str,
        fuzzy_threshold: int = 90,
        max_results_per_location: int = 1,
        preferred_countries: Optional[List[str]] = None,
        fuzzy: bool = True,
        max_ngram: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Resolve all location mentions found in a sentence and return detailed matches.

        Parameters
        ----------
        text : str
            Sentence or paragraph containing possible location mentions.
        fuzzy_threshold : int
            Minimum fuzzy score required for candidate acceptance.
        max_results_per_location : int
            Maximum number of results returned for each detected location.
        preferred_countries : Optional[List[str]]
            Optional country preference order for ranking.
        fuzzy : bool
            Whether to use fuzzy matching when direct parsing yields nothing.
        max_ngram : int
            Maximum n-gram size used while extracting place names from text.

        Returns
        -------
        List[Dict[str, Any]]
            Aggregated match list for all resolved location names in the text.
        """
        names = self.parse_locations(text, max_ngram=max_ngram, fuzzy_fallback=fuzzy)

        out: List[Dict[str, Any]] = []
        for name in names:
            out.extend(
                self.locate(
                    name,
                    fuzzy=fuzzy,
                    fuzzy_threshold=fuzzy_threshold,
                    max_results=max_results_per_location,
                    preferred_countries=preferred_countries,
                )
            )

        return out

    async def asentence_locations(
        self,
        text: str,
        fuzzy_threshold: int = 90,
        max_results_per_location: int = 1,
        preferred_countries: Optional[List[str]] = None,
        fuzzy: bool = True,
        max_ngram: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously resolve all location mentions found in a sentence.

        Parameters
        ----------
        text : str
            Sentence or paragraph containing possible location mentions.
        fuzzy_threshold : int
            Minimum fuzzy score required for candidate acceptance.
        max_results_per_location : int
            Maximum number of results returned for each detected location.
        preferred_countries : Optional[List[str]]
            Optional country preference order for ranking.
        fuzzy : bool
            Whether to use fuzzy matching when direct parsing yields nothing.
        max_ngram : int
            Maximum n-gram size used while extracting place names from text.

        Returns
        -------
        List[Dict[str, Any]]
            Aggregated match list for all resolved location names in the text.
        """
        return await asyncio.to_thread(
            self.sentence_locations,
            text,
            fuzzy_threshold,
            max_results_per_location,
            preferred_countries,
            fuzzy,
            max_ngram,
        )


if __name__ == "__main__":
    geo = Geolocator()
    geo.add_countries(["LB", "SY"])
    print("Geo client OK")
    print(geo.locate_in(query="Beirut", only=["LB", "SY"], fuzzy=True, threshold=85, limit=3))
