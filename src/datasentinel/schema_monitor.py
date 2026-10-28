"""Schema snapshots and drift detection."""


def get_schema(df) -> dict:
    return {c: str(t) for c, t in df.dtypes.items()}


def compare_schemas(old: dict, new: dict) -> dict:
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "type_changed": {c: (old[c], new[c]) for c in old if c in new and old[c] != new[c]},
    }


def has_drift(diff: dict) -> bool:
    return bool(diff["added"] or diff["removed"] or diff["type_changed"])
