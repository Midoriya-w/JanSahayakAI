import json
from pathlib import Path

from strands import tool


SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes" / "schemes.json"


def _load_schemes() -> tuple[list[dict], str | None]:
    """Load and validate the JSON-backed scheme records."""
    try:
        with SCHEMES_PATH.open(encoding="utf-8") as schemes_file:
            schemes = json.load(schemes_file)
    except FileNotFoundError:
        return [], f"Scheme data file not found: {SCHEMES_PATH}"
    except json.JSONDecodeError as error:
        return [], f"Scheme data contains invalid JSON: {error.msg}"
    except OSError as error:
        return [], f"Unable to read scheme data: {error}"

    if not isinstance(schemes, list) or not schemes:
        return [], "Scheme data is empty or is not a JSON array."
    if not all(isinstance(scheme, dict) for scheme in schemes):
        return [], "Scheme data must contain only scheme objects."
    return schemes, None


def _matches(value: object, requested: str | None) -> bool:
    return requested is None or str(value).casefold() == requested.casefold()


def _public_scheme(scheme: dict) -> dict:
    return {
        "scheme_id": scheme.get("scheme_id"),
        "name": scheme.get("name"),
        "category": scheme.get("category"),
        "state": scheme.get("state"),
        "description": scheme.get("description"),
        "benefits": scheme.get("benefits", []),
        "source": scheme.get("source"),
    }


def _find_scheme(schemes: list[dict], identifier: str) -> dict | None:
    """Find a scheme by ID or by an unambiguous name fragment."""
    if not isinstance(identifier, str) or not identifier.strip():
        return None

    requested = identifier.strip().casefold()
    exact_id = next(
        (scheme for scheme in schemes
         if str(scheme.get("scheme_id", "")).casefold() == requested),
        None,
    )
    if exact_id:
        return exact_id

    exact_name = next(
        (scheme for scheme in schemes
         if str(scheme.get("name", "")).casefold() == requested),
        None,
    )
    if exact_name:
        return exact_name

    name_matches = [
        scheme for scheme in schemes
        if requested in str(scheme.get("name", "")).casefold()
    ]
    return name_matches[0] if len(name_matches) == 1 else None


@tool
def search_schemes(category: str | None = None, location: str | None = None) -> str:
    """Search the JSON-backed government scheme knowledge source."""
    schemes, error = _load_schemes()
    if error:
        return json.dumps({"error": error})

    results = [
        _public_scheme(scheme)
        for scheme in schemes
        if _matches(scheme.get("category", ""), category)
        and (
            location is None
            or str(scheme.get("state", "")).casefold() in {"all", "india", "national"}
            or _matches(scheme.get("state", ""), location)
        )
    ]
    if not results:
        return json.dumps({
            "message": "No schemes found matching the requested category and location.",
            "category": category,
            "location": location,
        })
    return json.dumps(results, indent=2)


@tool
def search_government_schemes(state: str = None, **legacy_filters) -> str:
    """Backward-compatible wrapper for the previous scheme search tool."""
    return search_schemes(category=legacy_filters.get("category"), location=state)


@tool
def check_scheme_eligibility(scheme_id: str, user_data: dict) -> str:
    """Return a preliminary, non-binding comparison against stored requirements."""
    schemes, error = _load_schemes()
    if error:
        return json.dumps({"error": error})
    scheme = _find_scheme(schemes, scheme_id)
    if not scheme:
        return json.dumps({"error": f"Scheme {scheme_id} not found."})

    return json.dumps({
        "scheme_id": scheme.get("scheme_id"),
        "scheme_name": scheme.get("name"),
        "preliminary_status": "MORE_INFORMATION_NEEDED",
        "provided_information": user_data,
        "eligibility_to_verify": scheme.get("eligibility", {}),
        "verification_required": True,
        "source": scheme.get("source"),
        "note": "This tool does not make an official eligibility decision. Verify current requirements with the official source."
    }, indent=2)


@tool
def get_scheme_details(scheme_id: str) -> str:
    """Get full details for a scheme from the JSON knowledge source."""
    schemes, error = _load_schemes()
    if error:
        return json.dumps({"error": error})
    scheme = _find_scheme(schemes, scheme_id)
    if not scheme:
        return json.dumps({"error": f"Scheme {scheme_id} not found."})

    return json.dumps({
        **scheme,
        "important_note": "This data is an intermediate JSON prototype. Official verification is required."
    }, indent=2)
