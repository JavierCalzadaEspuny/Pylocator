"""Manual execution check for the pylocator package."""

import asyncio
from pprint import pprint

from pylocator import Geolocator


def show(title: str, value) -> None:
    print(f"\n== {title} ==")
    pprint(value)


async def run_async_checks(geo: Geolocator) -> None:
    await geo.aadd_countries(["US"])

    show(
        "Async locate",
        await geo.alocate("New York", fuzzy=True, fuzzy_threshold=80, max_results=3),
    )
    show(
        "Async locate in",
        await geo.alocate_in(
            "San Francisco",
            only=["US"],
            fuzzy=True,
            threshold=80,
            limit=3,
        ),
    )
    show(
        "Async sentence locations",
        await geo.asentence_locations(
            "I visited New York and San Francisco last year.",
            fuzzy_threshold=80,
            max_results_per_location=2,
            preferred_countries=["US"],
            fuzzy=True,
            max_ngram=3,
        ),
    )


def main() -> None:
    geo = Geolocator()

    show("Singleton object", geo)

    geo.add_countries(["LB", "SY"])
    show("Active countries after add_countries", sorted(geo.active_countries))

    english_text = "A fire was reported near Beirut and Tripoli overnight."
    arabic_text = "تم الإبلاغ عن حريق قرب بيروت وطرابلس الليلة الماضية."
    mixed_text = "Explosion near Beirut and دمشق during the night."

    show(
        "parse_locations English",
        geo.parse_locations(english_text, max_ngram=3, fuzzy_fallback=True),
    )
    show(
        "parse_locations Arabic",
        geo.parse_locations(arabic_text, max_ngram=3, fuzzy_fallback=True),
    )
    show(
        "parse_locations mixed",
        geo.parse_locations(mixed_text, max_ngram=3, fuzzy_fallback=True),
    )

    show(
        "locate Beirut",
        geo.locate("Beirut", fuzzy=True, fuzzy_threshold=85, max_results=3),
    )
    show(
        "locate Arabic query",
        geo.locate("بيروت", fuzzy=True, fuzzy_threshold=85, max_results=3),
    )
    show(
        "locate compound name",
        geo.locate("New York", fuzzy=True, fuzzy_threshold=80, max_results=3),
    )

    show(
        "locate_in Lebanon and Syria",
        geo.locate_in(
            query="Tripoli",
            only=["LB", "SY"],
            fuzzy=True,
            threshold=85,
            limit=5,
            prefer=["LB", "SY"],
        ),
    )
    show(
        "sentence_locations English",
        geo.sentence_locations(
            "Beirut and Tripoli were mentioned in the report.",
            fuzzy_threshold=85,
            max_results_per_location=2,
            preferred_countries=["LB", "SY"],
            fuzzy=True,
            max_ngram=3,
        ),
    )
    show(
        "sentence_locations Arabic",
        geo.sentence_locations(
            "بيروت وطرابلس كانتا ضمن التقرير.",
            fuzzy_threshold=85,
            max_results_per_location=2,
            preferred_countries=["LB", "SY"],
            fuzzy=True,
            max_ngram=3,
        ),
    )
    show(
        "sentence_locations mixed",
        geo.sentence_locations(
            "Beirut and بيروت both appear in the same sentence.",
            fuzzy_threshold=85,
            max_results_per_location=2,
            preferred_countries=["LB", "SY"],
            fuzzy=True,
            max_ngram=2,
        ),
    )

    asyncio.run(run_async_checks(geo))


if __name__ == "__main__":
    main()
