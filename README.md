# Pylocator

Pylocator is a lightweight geolocation library powered by GeoNames data. It includes multilingual normalization, Arabic-friendly matching, fuzzy search, and a singleton `Geolocator` client designed for linear use.

## What It Does

- Loads country data from GeoNames.
- Normalizes English, Arabic, and mixed text.
- Extracts place names from sentences.
- Resolves exact and fuzzy location matches.
- Keeps one shared `Geolocator` instance for the whole process.

## Install

Repository links:

- Web: https://github.com/JavierCalzadaEspuny/Pylocator
- Git clone: https://github.com/JavierCalzadaEspuny/Pylocator.git

Install directly from GitHub (recommended for consumers):

```bash
uv add git+https://github.com/JavierCalzadaEspuny/Pylocator.git
```

Or with pip:

```bash
pip install git+https://github.com/JavierCalzadaEspuny/Pylocator.git
```

For local development (clone + editable install):

```bash
git clone https://github.com/JavierCalzadaEspuny/Pylocator.git
cd Pylocator
```

Then install in editable mode:

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

results = geo.locate("Beirut", max_results=3, fuzzy=True, fuzzy_threshold=85)
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
locations = geo.parse_locations(text, max_ngram=3, only="LB", fuzzy_fallback=True)
matches = geo.sentence_locations(
	text,
	max_results_per_location=2,
	only="LB",
	preferred_countries=["LB"],
	fuzzy=True,
	fuzzy_threshold=85,
	max_ngram=3,
)

print(locations)
print(matches)
```

You can keep reusing the same object and add countries later:

```python
geo = Geolocator()
geo.add_countries(["LB"])
geo.add_countries(["SY"])
```

## Methods Reference (Real Output From `smoke_run.py`)

The blocks below use the exact method examples and output printed by:

```bash
uv run python smoke_run.py
```

### Method: `Geolocator()`

Example:

```text
g1 is g2
```

Output:

```text
True
```

### Method: `add_countries(codes)`

Example:

```text
add_countries(['LB', 'SY'])
```

Output:

```text
['LB', 'SY']
```

### Method: `aadd_countries(codes)`

Example:

```text
await aadd_countries(['US'])
```

Output:

```text
['LB', 'SY', 'US']
```

### Method: `parse_locations(text, max_ngram=4, only=None, fuzzy_fallback=True)`

Example:

```text
parse_locations(english_text, max_ngram=3, fuzzy_fallback=True)
```

Output:

```text
['Washington', 'Beyrouth', 'Anderson', 'Tripoli']
```

Example:

```text
parse_locations(arabic_text, max_ngram=3, fuzzy_fallback=True)
```

Output:

```text
['Harîq', 'Beirut']
```

Example:

```text
parse_locations(mixed_text, max_ngram=3, fuzzy_fallback=True)
```

Output:

```text
['Beyrouth', 'Anderson', 'Damascus Governorate', 'Pocket Recreation Area', 'Night']
```

Example:

```text
parse_locations('Tripoli and Damascus were mentioned.', max_ngram=3, only='LB', fuzzy_fallback=True)
```

Output:

```text
['Tripoli']
```

### Method: `aparse_locations(text, max_ngram=4, only=None, fuzzy_fallback=True)`

Example:

```text
await aparse_locations('Tripoli and Damascus were mentioned.', max_ngram=3, only='LB')
```

Output:

```text
['Tripoli']
```

### Method: `locate(place_name, max_results=10, only=None, preferred_countries=None, fuzzy=False, fuzzy_threshold=90)`

Example:

```text
locate('Beirut', max_results=3, only='LB', fuzzy=True, fuzzy_threshold=85)
```

Output:

```text
[{'name': 'Beyrouth', 'country': 'LB', 'match_score': 100}, {'name': 'Beirut', 'country': 'LB', 'match_score': 100}]
```

Example:

```text
locate('بيروت', max_results=3, only='LB', fuzzy=True, fuzzy_threshold=85)
```

Output:

```text
[{'name': 'Beirut', 'country': 'LB', 'match_score': 100}]
```

### Method: `locate_in(query, limit=10, *, only, prefer=None, fuzzy=False, threshold=90)`

Example:

```text
locate_in('Tripoli', limit=3, only=['LB', 'SY'], fuzzy=True, threshold=85)
```

Output:

```text
[{'name': 'Tripoli', 'country': 'LB', 'match_score': 100}, {'name': 'Tripoli District', 'country': 'LB', 'match_score': 100}, {'name': 'Tripoli', 'country': 'LB', 'match_score': 100}]
```

### Method: `sentence_locations(text, max_results_per_location=1, only=None, preferred_countries=None, fuzzy=True, fuzzy_threshold=90, max_ngram=4)`

Example:

```text
sentence_locations(english_text, max_results_per_location=2, preferred_countries=['LB', 'SY'], fuzzy=True, fuzzy_threshold=85, max_ngram=3)
```

Output:

```text
[{'name': 'Washington', 'country': 'US', 'match_score': 100}, {'name': 'Washington', 'country': 'US', 'match_score': 100}, {'name': 'Beyrouth', 'country': 'LB', 'match_score': 100}, {'name': 'Beirut', 'country': 'LB', 'match_score': 100}]
```

Example:

```text
sentence_locations('Tripoli and Damascus were mentioned.', max_results_per_location=2, only='LB', preferred_countries=['LB', 'SY'], fuzzy=True, fuzzy_threshold=85, max_ngram=3)
```

Output:

```text
[{'name': 'Tripoli', 'country': 'LB', 'match_score': 100}, {'name': 'Tripoli District', 'country': 'LB', 'match_score': 100}]
```

### Method: `alocate(place_name, max_results=10, only=None, preferred_countries=None, fuzzy=True, fuzzy_threshold=90)`

Example:

```text
await alocate('New York', max_results=3, only='US', fuzzy=True, fuzzy_threshold=80)
```

Output:

```text
[{'name': 'New York', 'country': 'US', 'match_score': 100}, {'name': 'New York City', 'country': 'US', 'match_score': 100}, {'name': 'New York County', 'country': 'US', 'match_score': 100}]
```

### Method: `alocate_in(query, limit=10, *, only, prefer=None, fuzzy=True, threshold=90)`

Example:

```text
await alocate_in('San Francisco', limit=3, only=['US'], fuzzy=True, threshold=80)
```

Output:

```text
[{'name': 'San Francisco', 'country': 'US', 'match_score': 100}, {'name': 'San Francisco', 'country': 'US', 'match_score': 100}, {'name': 'La Valley', 'country': 'US', 'match_score': 100}]
```

### Method: `asentence_locations(text, max_results_per_location=1, only=None, preferred_countries=None, fuzzy=True, fuzzy_threshold=90, max_ngram=4)`

Example:

```text
await asentence_locations('I visited New York and Beirut.', max_results_per_location=2, only='US', preferred_countries=['US', 'LB'], fuzzy=True, fuzzy_threshold=80, max_ngram=3)
```

Output:

```text
[{'name': 'New York', 'country': 'US', 'match_score': 100}, {'name': 'New York City', 'country': 'US', 'match_score': 100}, {'name': 'Anderson County', 'country': 'US', 'match_score': 100}, {'name': 'Anderson County', 'country': 'US', 'match_score': 100}]
```

## Examples

### English text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["US"])

print(geo.parse_locations("New York and San Francisco were mentioned in the report.", max_ngram=3))
print(geo.locate("New York", max_results=3, fuzzy=True, fuzzy_threshold=80))
```

Strict country filter from sentence text:

```python
print(geo.parse_locations("Tripoli and Damascus were mentioned in the report.", max_ngram=3, only="LB"))
```

### Arabic text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB", "SY"])

print(geo.parse_locations("تم الإبلاغ عن حريق قرب بيروت وطرابلس الليلة الماضية.", max_ngram=3))
print(geo.locate("بيروت", max_results=3, fuzzy=True, fuzzy_threshold=85))
```

### Mixed text

```python
from pylocator import Geolocator

geo = Geolocator()
geo.add_countries(["LB", "US"])

text = "Explosion near Beirut and New York during the night."
print(results)

results = geo.locate("Beirut", max_results=3, fuzzy=True, fuzzy_threshold=85)
print(
	geo.sentence_locations(
		text,
		max_results_per_location=2,
		only=["LB"],
		preferred_countries=["LB", "US"],
		fuzzy=True,
		fuzzy_threshold=85,
		max_ngram=3,
	)
)
```

## Async Use

```python
import asyncio
from pylocator import Geolocator


async def main() -> None:
	geo = Geolocator()
	await geo.aadd_countries(["LB", "US"])

	print(await geo.alocate("New York", max_results=3, fuzzy=True, fuzzy_threshold=80))
	print(await geo.asentence_locations("I visited New York and Beirut.", max_results_per_location=2, only=["US"], fuzzy=True, fuzzy_threshold=80, max_ngram=3))


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
