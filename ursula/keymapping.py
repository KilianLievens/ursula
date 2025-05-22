def map_keys(key: str, layout: str = "azerty") -> str:
    """Map a keyboard key to the appropriate character based on the current layout"""
    # Key mappings for AZERTY layout
    azerty_mappings = {
        "a": "q",
        "q": "a",
        "z": "w",
        "w": "z",
        "m": ",",
        ",": "?",
        ";": "m",
        ".": ";",
        "/": "!",
        "[": "^",
        "]": "$",
        "\\": "*",
        "'": "ù",
        "-": ")",
        "=": "=",
        "`": "ù",
    }

    return azerty_mappings.get(key, key) if layout == "azerty" else key
