from ursula.keymapping.keymap import Keymap


class Azerty(Keymap):
    def map(self, key: str, is_shift_pressed: bool) -> str:
        azerty_letter_mappings = {
            "a": "q",
            "q": "a",
            "z": "w",
            "w": "z",
            "m": ",",
            ";": "m",
        }

        azerty_number_mappings = {
            "1": "&",
            "2": "é",
            "3": '"',
            "4": "'",
            "5": "(",
            "6": "-",
            "7": "è",
            "8": "_",
            "9": "ç",
            "0": "à",
            "-": ")",
            "=": "=",
        }

        azerty_number_shift_mappings = {
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "0": "0",
            "-": "°",
            "=": "+",
        }

        azerty_punctuation_mappings = {
            ",": "?",
            ".": ";",
            "/": "!",
            "'": "ù",
            "[": "^",
            "]": "$",
            "\\": "*",
            "`": "²",
        }

        azerty_punctuation_shift_mappings = {
            ",": ".",
            ".": ":",
            "/": "§",
            "'": "%",
            "[": "¨",
            "]": "£",
            "\\": "µ",
            "`": "³",
        }

        if key in azerty_letter_mappings or key.isalpha():
            mapped_key = azerty_letter_mappings.get(key, key)
            return mapped_key.upper() if is_shift_pressed else mapped_key

        if key in azerty_number_mappings:
            if is_shift_pressed:
                return azerty_number_shift_mappings.get(key, key)
            else:
                return azerty_number_mappings.get(key, key)

        if key in azerty_punctuation_mappings:
            if is_shift_pressed:
                return azerty_punctuation_shift_mappings.get(key, key)
            else:
                return azerty_punctuation_mappings.get(key, key)

        return key
