# Pylocator

Pylocator is a lightweight geolocation library powered by GeoNames data. It includes multilingual normalization, Arabic-friendly matching, fuzzy search, and a singleton `Geolocator` client designed for linear use.

## What It Does

- Loads country data from GeoNames.
- Normalizes English, Arabic, and mixed text.
- Extracts place names from sentences.
- Resolves exact and fuzzy location matches.
- Keeps one shared `Geolocator` instance for the whole process.

## Install

For local development:

```bash
pip install -e .
```

With `uv`:

```bash
uv sync
```

## Basic Use

The intended workflow is linear: create the object, load countries, then call the methods you need.

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB", "SY"])

results = geo.locate("Beirut", fuzzy=True, fuzzy_threshold=85, max_results=3)
print(results)
```

The class is a singleton, so every call to `Geolocator()` returns the same shared object.

## Linear Workflow

This is the recommended way to use the library during development and in production.

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB"])

text = "A fire was reported near Beirut and Tripoli overnight."
locations = geo.parse_locations(text, max_ngram=3, fuzzy_fallback=True)
matches = geo.sentence_locations(text, fuzzy_threshold=85, max_results_per_location=2, preferred_countries=["LB"])

print(locations)
print(matches)
```

You can keep reusing the same object and add countries later:

```python
geo = Geolocator()
geo.add_countries(["LB"])
geo.add_countries(["SY"])
```

## Public API

### `Geolocator()`

Creates or returns the shared singleton instance.

### `add_countries(codes)`

Loads and activates one or more country datasets.

### `aadd_countries(codes)`

Async version of `add_countries`.

### `parse_locations(text, max_ngram=4, fuzzy_fallback=True)`

Extracts place names from a sentence or paragraph.

### `aparse_locations(text, max_ngram=4, fuzzy_fallback=True)`

Async version of `parse_locations`.

### `locate(place_name, fuzzy=False, fuzzy_threshold=90, max_results=10, preferred_countries=None)`

Searches the active index for a place name.

### `locate_in(query, only, fuzzy=False, threshold=90, limit=10, prefer=None)`

Searches within a restricted country list.

### `alocate(place_name, fuzzy=True, fuzzy_threshold=90, max_results=10, preferred_countries=None)`

Async version of `locate`.

### `alocate_in(query, only, fuzzy=True, threshold=90, limit=10, prefer=None)`

Async version of `locate_in`.

### `sentence_locations(text, fuzzy_threshold=90, max_results_per_location=1, preferred_countries=None, fuzzy=True, max_ngram=4)`

Extracts all locations from a sentence and resolves them.

### `asentence_locations(text, fuzzy_threshold=90, max_results_per_location=1, preferred_countries=None, fuzzy=True, max_ngram=4)`

Async version of `sentence_locations`.

## Examples

### English text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["US"])

print(geo.parse_locations("New York and San Francisco were mentioned in the report.", max_ngram=3))
print(geo.locate("New York", fuzzy=True, fuzzy_threshold=80, max_results=3))
```

### Arabic text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB", "SY"])

print(geo.parse_locations("تم الإبلاغ عن حريق قرب بيروت وطرابلس الليلة الماضية.", max_ngram=3))
print(geo.locate("بيروت", fuzzy=True, fuzzy_threshold=85, max_results=3))
```

### Mixed text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB", "US"])

text = "Explosion near Beirut and New York during the night."
print(geo.sentence_locations(text, fuzzy_threshold=85, max_results_per_location=2, preferred_countries=["LB", "US"], fuzzy=True, max_ngram=3))
```

## Async Use

```python
import asyncio
from pylocator import Geolocator


async def main() -> None:
	geo = Geolocator()
	await geo.aadd_countries(["LB", "US"])

	print(await geo.alocate("New York", fuzzy=True, fuzzy_threshold=80, max_results=3))
	print(await geo.asentence_locations("I visited New York and Beirut.", fuzzy_threshold=80, max_results_per_location=2, fuzzy=True, max_ngram=3))


asyncio.run(main())
```

## Manual Smoke Test

Run the included smoke script to exercise the main paths and inspect the output:

```bash
uv run python smoke_run.py
```

It covers:

- Singleton initialization.
- Country loading.
- Exact and fuzzy searches.
- English, Arabic, and mixed text.
- Linear and async usage.

## Project Structure

- [src/pylocator/](src/pylocator/) contains the package code.
- [smoke_run.py](smoke_run.py) is the manual verification script.
- [pyproject.toml](pyproject.toml) defines packaging and dependencies.

## Notes

- The `Geolocator` instance is shared across the process.
- Start with `Geolocator()`, then call `add_countries()` explicitly.
- `max_ngram` is configured per extraction call, not on the constructor.
- Country data is cached automatically by the internal manager.
