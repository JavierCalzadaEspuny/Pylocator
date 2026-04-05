"""Linear smoke test that demonstrates every public Geolocator method and output."""

import asyncio

from pylocator import Geolocator


def compact(results: list[dict], limit: int = 3) -> list[dict]:
    """Keep only key fields so smoke output is readable and stable."""
    return [
        {
            "name": r.get("name"),
            "country": r.get("country"),
            "match_score": r.get("match_score"),
        }
        for r in results[:limit]
    ]


def show(method: str, example: str, output) -> None:
    print(f"\nMETHOD: {method}")
    print(f"EXAMPLE: {example}")
    print(f"OUTPUT: {output}")


async def main() -> None:
    # One singleton instance, then all methods executed linearly.
    geo = Geolocator()
    other = Geolocator()

    show("Geolocator()", "g1 is g2", geo is other)

    geo.add_countries(["LB", "SY"])
    show("add_countries", "add_countries(['LB', 'SY'])", sorted(geo.active_countries))

    await geo.aadd_countries(["US"])
    show("aadd_countries", "await aadd_countries(['US'])", sorted(geo.active_countries))

    english_text = "A fire was reported near Beirut and Tripoli overnight."
    arabic_text = "تم الإبلاغ عن حريق قرب بيروت وطرابلس الليلة الماضية."
    mixed_text = "Explosion near Beirut and دمشق during the night."

    show(
        "parse_locations",
        "parse_locations(english_text, max_ngram=3, fuzzy_fallback=True)",
        geo.parse_locations(english_text, max_ngram=3, fuzzy_fallback=True),
    )
    show(
        "parse_locations",
        "parse_locations(arabic_text, max_ngram=3, fuzzy_fallback=True)",
        geo.parse_locations(arabic_text, max_ngram=3, fuzzy_fallback=True),
    )
    show(
        "parse_locations",
        "parse_locations(mixed_text, max_ngram=3, fuzzy_fallback=True)",
        geo.parse_locations(mixed_text, max_ngram=3, fuzzy_fallback=True),
    )
    show(
        "parse_locations",
        "parse_locations('Tripoli and Damascus were mentioned.', only='LB', max_ngram=3, fuzzy_fallback=True)",
        geo.parse_locations(
            "Tripoli and Damascus were mentioned.",
            only="LB",
            max_ngram=3,
            fuzzy_fallback=True,
        ),
    )

    show(
        "aparse_locations",
        "await aparse_locations('I visited New York and Beirut.', max_ngram=3)",
        await geo.aparse_locations("I visited New York and Beirut.", max_ngram=3),
    )

    show(
        "locate",
        "locate('Beirut', fuzzy=True, fuzzy_threshold=85, max_results=3)",
        compact(geo.locate("Beirut", fuzzy=True, fuzzy_threshold=85, max_results=3)),
    )
    show(
        "locate",
        "locate('بيروت', fuzzy=True, fuzzy_threshold=85, max_results=3)",
        compact(geo.locate("بيروت", fuzzy=True, fuzzy_threshold=85, max_results=3)),
    )

    show(
        "locate_in",
        "locate_in('Tripoli', only=['LB', 'SY'], fuzzy=True, threshold=85, limit=3)",
        compact(
            geo.locate_in(
                query="Tripoli",
                only=["LB", "SY"],
                fuzzy=True,
                threshold=85,
                limit=3,
            )
        ),
    )

    show(
        "sentence_locations",
        "sentence_locations(english_text, fuzzy_threshold=85, max_results_per_location=2, preferred_countries=['LB', 'SY'], fuzzy=True, max_ngram=3)",
        compact(
            geo.sentence_locations(
                english_text,
                fuzzy_threshold=85,
                max_results_per_location=2,
                preferred_countries=["LB", "SY"],
                fuzzy=True,
                max_ngram=3,
            ),
            limit=4,
        ),
    )

    show(
        "sentence_locations",
        "sentence_locations('Tripoli and Damascus were mentioned.', only='LB', fuzzy_threshold=85, max_results_per_location=2, preferred_countries=['LB', 'SY'], fuzzy=True, max_ngram=3)",
        compact(
            geo.sentence_locations(
                "Tripoli and Damascus were mentioned.",
                only="LB",
                fuzzy_threshold=85,
                max_results_per_location=2,
                preferred_countries=["LB", "SY"],
                fuzzy=True,
                max_ngram=3,
            ),
            limit=4,
        ),
    )

    show(
        "alocate",
        "await alocate('New York', fuzzy=True, fuzzy_threshold=80, max_results=3)",
        compact(await geo.alocate("New York", fuzzy=True, fuzzy_threshold=80, max_results=3)),
    )

    show(
        "alocate_in",
        "await alocate_in('San Francisco', only=['US'], fuzzy=True, threshold=80, limit=3)",
        compact(
            await geo.alocate_in(
                "San Francisco",
                only=["US"],
                fuzzy=True,
                threshold=80,
                limit=3,
            )
        ),
    )

    show(
        "asentence_locations",
        "await asentence_locations('I visited New York and Beirut.', fuzzy_threshold=80, max_results_per_location=2, preferred_countries=['US', 'LB'], fuzzy=True, max_ngram=3)",
        compact(
            await geo.asentence_locations(
                "I visited New York and Beirut.",
                fuzzy_threshold=80,
                max_results_per_location=2,
                preferred_countries=["US", "LB"],
                fuzzy=True,
                max_ngram=3,
            ),
            limit=4,
        ),
    )

    show(
        "asentence_locations",
        "await asentence_locations('Tripoli and Damascus were mentioned.', only='LB', fuzzy_threshold=85, max_results_per_location=2, preferred_countries=['LB', 'SY'], fuzzy=True, max_ngram=3)",
        compact(
            await geo.asentence_locations(
                "Tripoli and Damascus were mentioned.",
                only="LB",
                fuzzy_threshold=85,
                max_results_per_location=2,
                preferred_countries=["LB", "SY"],
                fuzzy=True,
                max_ngram=3,
            ),
            limit=4,
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
