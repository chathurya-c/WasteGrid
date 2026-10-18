import pandas as pd

SAMPLE_SOURCES = [
    {"id": "household", "baseline_kg": 2000, "waste_type": "wet", "modifier": 1.0},
    {"id": "office", "baseline_kg": 800, "waste_type": "dry", "modifier": 1.0},
    {"id": "restaurant", "baseline_kg": 1500, "waste_type": "wet", "modifier": 1.2},
    {"id": "college", "baseline_kg": 600, "waste_type": "dry", "modifier": 1.0},
    {"id": "event", "baseline_kg": 0, "waste_type": "wet", "modifier": 1.0},
]

FACILITIES = [
    {
        "id": "A",
        "accepts": "wet",
        "capacity_kg": 3000,
        "current_load_kg": 0,
        "distance_km": 5,
    },
    {
        "id": "B",
        "accepts": "wet",
        "capacity_kg": 1500,
        "current_load_kg": 0,
        "distance_km": 8,
    },
    {
        "id": "C",
        "accepts": "dry",
        "capacity_kg": 2500,
        "current_load_kg": 0,
        "distance_km": 6,
    },
]

EVENT_SPIKE_KG = 4000


def load_sources_from_csv(uploaded_file):
    """Parse an uploaded CSV into the internal source format with flexible column matching."""
    df = pd.read_csv(uploaded_file)
    # Normalize column names to lowercase
    col_map = {str(c).strip().lower(): c for c in df.columns}

    # Identify key columns
    src_col = (
        col_map.get("source")
        or col_map.get("name")
        or col_map.get("id")
        or df.columns[0]
    )
    base_col = (
        col_map.get("baseline_kg")
        or col_map.get("kg")
        or col_map.get("weight_kg")
        or col_map.get("amount_kg")
        or df.columns[1]
    )
    type_col = (
        col_map.get("waste_type")
        or col_map.get("type")
        or col_map.get("category")
        or (df.columns[2] if len(df.columns) > 2 else None)
    )

    sources = []
    for _, row in df.iterrows():
        raw_type = str(row[type_col]).strip().lower() if type_col else "wet"
        waste_type = "dry" if "dry" in raw_type or "rec" in raw_type else "wet"
        sources.append(
            {
                "id": str(row[src_col]).strip(),
                "baseline_kg": float(row[base_col]),
                "waste_type": waste_type,
                "modifier": 1.0,
            }
        )
    return sources


def apply_event_state(sources, event_active):
    """If an event is active, inject the spike into the event source or append one."""
    out = []
    has_event = False
    for s in sources:
        s = dict(s)
        if s["id"].lower() == "event":
            has_event = True
            if event_active:
                s["baseline_kg"] = EVENT_SPIKE_KG
        out.append(s)

    if event_active and not has_event:
        out.append(
            {
                "id": "event",
                "baseline_kg": EVENT_SPIKE_KG,
                "waste_type": "wet",
                "modifier": 1.0,
            }
        )
    return out


def totals(sources):
    """Compute wet, dry, and total waste from the source list."""
    wet = sum(
        s["baseline_kg"] * s.get("modifier", 1.0)
        for s in sources
        if s.get("waste_type") == "wet"
    )
    dry = sum(
        s["baseline_kg"] * s.get("modifier", 1.0)
        for s in sources
        if s.get("waste_type") == "dry"
    )
    return wet, dry, wet + dry
