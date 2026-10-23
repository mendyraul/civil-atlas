"""Inbound license gate: only data we may redistribute under ODbL 1.0 can be imported.

See docs/licensing-register.md. Non-commercial, no-derivatives, GPL and CC BY-SA
sources are reference-only and are refused here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class License:
    spdx: str
    url: str
    requires_attribution: bool


ALLOWED = (
    License("CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/", False),
    License("PDDL-1.0", "https://opendatacommons.org/licenses/pddl/1-0/", False),
    License("CC-BY-3.0", "https://creativecommons.org/licenses/by/3.0/", True),
    License("CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/", True),
    License("ODbL-1.0", "https://opendatacommons.org/licenses/odbl/1-0/", True),
)


def _normalize(value: str) -> str:
    value = value.strip().lower().replace("http://", "https://")
    for suffix in ("legalcode", "legalcode.txt"):
        if value.endswith(suffix):
            value = value[: -len(suffix)]
    return value.rstrip("/")


def resolve_license(value: str) -> License:
    """Return the allowlisted license for an SPDX ID or canonical URL, or raise."""
    key = _normalize(value)
    for allowed in ALLOWED:
        if key in {allowed.spdx.lower(), _normalize(allowed.url)}:
            return allowed
    raise ValueError(
        f"license {value!r} is not cleared for import; only CC0, PDDL, CC BY 3.0/4.0 and "
        "ODbL data may enter the ODbL database (see docs/licensing-register.md)"
    )


def check_license(adapter: object) -> License:
    value = getattr(adapter, "license", None)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{type(adapter).__name__} must declare its source license")
    return resolve_license(value)
