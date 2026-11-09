# SPDX-License-Identifier: GPL-2.0-or-later
"""Versioned explicit classification, independent of source geometry and styling.

No vendor codes or units are inferred/converted. Unknown source values survive.
This foundation is opt-in; existing dataset roles and catalogue v1 are unchanged.
"""
from copy import deepcopy

VERSION = 1
MAPPING_RULE = "explicit-selection-v1"
OPERATION_FAMILIES = {
    "tillage": "tillage", "planting": "planting", "spraying": "application",
    "spreading": "application", "harvesting": "harvesting",
}


def classify(source, *, operation="unknown", purpose="unknown", measurement="", unit="",
             semantics="unknown", field_id="", season_id=""):
    """Record an explicit selection; source is a JSON-compatible provenance object.

Measurement/unit tokens remain verbatim; even a familiar unit does not establish
what variable it measures. Context is an unresolved identifier, not a guessed link.
"""
    return {"version": VERSION, "mapping_rule": MAPPING_RULE,
            "purpose": purpose, "operation_family": OPERATION_FAMILIES.get(operation, "unknown"),
            "operation_subtype": operation, "measurement": measurement, "unit": unit,
            "semantics": semantics, "field_id": field_id, "season_id": season_id,
            "source": deepcopy(source)}
