from yarns.models import YarnType


def normalize_yarn_type(raw_type: str) -> str:
    """
    Normalize yarn type/weight strings to YarnType choices.
    Handles common terminology from various sources.
    Returns empty string if no match found.
    """
    if not raw_type:
        return ""

    raw = raw_type.strip().lower()

    # Direct matches to YarnType choices
    choices_map = {
        "lace": YarnType.LACE,
        "fingering": YarnType.FINGERING,
        "sport": YarnType.SPORT,
        "dk": YarnType.DK,
        "worsted": YarnType.WORSTED,
        "aran": YarnType.ARAN,
        "bulky": YarnType.BULKY,
        "super bulky": YarnType.SUPER_BULKY,
        "superbulky": YarnType.SUPER_BULKY,
        "jumbo": YarnType.JUMBO,
    }

    # Check direct matches
    if raw in choices_map:
        return choices_map[raw]

    # Check partial matches (weight ranges often include these terms)
    for key, value in choices_map.items():
        if key in raw:
            return value

    # Common alternative names
    if any(term in raw for term in ["2-ply", "fingering weight", "sock"]):
        return YarnType.FINGERING
    if any(term in raw for term in ["4-ply", "sport weight"]):
        return YarnType.SPORT
    if any(term in raw for term in ["8-ply", "double knit", "dk weight"]):
        return YarnType.DK
    if any(term in raw for term in ["10-ply", "worsted weight", "weight", "medium"]):
        return YarnType.WORSTED
    if any(term in raw for term in ["aran weight", "12-ply"]):
        return YarnType.ARAN
    if any(term in raw for term in ["bulky weight", "chunky"]):
        return YarnType.BULKY
    if any(term in raw for term in ["super bulky", "super chunky", "roving"]):
        return YarnType.SUPER_BULKY

    return ""
