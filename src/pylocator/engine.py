"""Core normalization, tokenization, and matching logic for geolocation search."""

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set

from pyarabic import araby
from rapidfuzz import fuzz, process

from .models import ARABIC_FALLBACK, PUNCT_PATTERN, TOKEN_PATTERN, Place


class GeoEngine:
    """
    Provides text normalization and place matching over prepared geolocation indexes.

    Methods
    -------
    normalize(value): Normalize multilingual text for stable matching.
    tokenize(text): Split normalized text into searchable tokens.
    iter_ngrams(tokens, max_n): Yield n-gram phrases from token lists.
    country_ranker(pref): Build a ranking function for preferred countries.
    locate(q, idx, fz, thr, top, pref): Find best matching places from an index.

    Example
    -------
    >>> engine = GeoEngine()
    >>> engine.normalize("انفجار قرب بيروت")
    'انفجار قرب بيروت'
    """

    @staticmethod
    def normalize(value: str) -> str:
        """
        Normalize text by removing noise and harmonizing Arabic and Unicode variations.

        Parameters
        ----------
        value : str
            Raw user text that may contain punctuation, diacritics, or mixed forms.

        Returns
        -------
        str
            Normalized text ready to be used as a search key.
        """
        text = unicodedata.normalize("NFKD", value)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))

        text = araby.normalize_ligature(text)
        text = araby.normalize_hamza(text)
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
        text = "".join(ARABIC_FALLBACK.get(ch, ch) for ch in text)

        text = text.casefold()
        text = PUNCT_PATTERN.sub(" ", text)
        text = re.sub(r"_", " ", text)
        return " ".join(text.split())

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Extract searchable word tokens from input text.

        Parameters
        ----------
        text : str
            Input text to split into tokens.

        Returns
        -------
        List[str]
            Ordered token list used by n-gram matching.
        """
        return TOKEN_PATTERN.findall(text)

    @staticmethod
    def iter_ngrams(tokens: List[str], max_n: int) -> Iterable[tuple[int, int, str]]:
        """
        Yield descending-length n-gram windows over tokenized text.

        Parameters
        ----------
        tokens : List[str]
            Token sequence generated from a source sentence.
        max_n : int
            Maximum n-gram size to emit.

        Returns
        -------
        Iterable[tuple[int, int, str]]
            Tuples of start index, n-gram length, and phrase text.
        """
        if not tokens:
            return

        limit = min(max(1, max_n), len(tokens))
        for n in range(limit, 0, -1):
            for i in range(0, len(tokens) - n + 1):
                yield i, n, " ".join(tokens[i : i + n])

    @staticmethod
    def country_ranker(pref: Optional[List[str]] = None):
        """
        Create a country-priority ranking function for result ordering.

        Parameters
        ----------
        pref : Optional[List[str]]
            Ordered country preference list, where earlier codes rank higher.

        Returns
        -------
        callable
            Function that maps a country code to an integer rank.
        """
        if not pref:
            return lambda _: 0

        prio = {code.upper(): i for i, code in enumerate(pref)}
        default_rank = len(prio)
        return lambda code: prio.get(code.upper(), default_rank)

    def locate(
        self,
        q: str,
        idx: Dict[str, List[Place]],
        fz: bool,
        thr: int,
        top: int,
        pref: Optional[List[str]] = None,
        allowed_countries: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Locate places by exact or fuzzy matching against a normalized index.

        Parameters
        ----------
        q : str
            Query text representing a place name.
        idx : Dict[str, List[Place]]
            Normalized lookup index keyed by normalized place string.
        fz : bool
            Whether fuzzy search fallback is allowed when exact match fails.
        thr : int
            Fuzzy match threshold in the range 0-100.
        top : int
            Maximum number of matches to return.
        pref : Optional[List[str]]
            Optional preferred country order used for ranking.
        allowed_countries : Optional[Set[str]]
            Optional country whitelist applied as a post-filter on matched places.

        Returns
        -------
        List[Dict[str, Any]]
            Ranked result dictionaries including coordinates, metadata, and score.
        """
        norm_q = self.normalize(q)
        if not norm_q or not idx:
            return []

        rank_country = self.country_ranker(pref)

        def as_result(place: Place, score: int) -> Dict[str, Any]:
            return {
                "name": place.name,
                "lat": place.lat,
                "lon": place.lon,
                "population": place.population,
                "country": place.country,
                "feature_class": place.feature_class,
                "feature_type": place.feature_type,
                "match_score": score,
            }

        exact = idx.get(norm_q, [])
        if allowed_countries is not None:
            exact = [p for p in exact if p.country in allowed_countries]
        if exact:
            out = [as_result(p, 100) for p in exact]
            out.sort(key=lambda x: (rank_country(x["country"]), -x["population"]))
            return out[:top]

        if not fz:
            return []

        cutoff = max(0, min(100, thr))
        key_matches = process.extract(
            norm_q,
            idx.keys(),
            scorer=fuzz.ratio,
            score_cutoff=cutoff,
            limit=200,
        )

        scored: Dict[int, Dict[str, Any]] = {}
        for key, score, _ in key_matches:
            score_i = int(score)
            for place in idx[key]:
                if allowed_countries is not None and place.country not in allowed_countries:
                    continue
                old = scored.get(place.geonameid)
                now = as_result(place, score_i)
                if old is None or now["match_score"] > old["match_score"]:
                    scored[place.geonameid] = now

        out = sorted(
            scored.values(),
            key=lambda x: (
                rank_country(x["country"]),
                -x["match_score"],
                -x["population"],
            ),
        )
        return out[:top]


if __name__ == "__main__":
    eng = GeoEngine()
    print("Geo engine OK")
    print(eng.normalize("انفجار قرب بيروت"))
