from ursula.keymapping.keymap import Keymap


class Qwerty(Keymap):
    def map(self, key: str, is_shift_pressed: bool) -> str:
        if key.isalpha():
            return key.upper() if is_shift_pressed else key.lower()

        qwerty_number_mappings = {
            "1": "!",
            "2": "@",
            "3": "#",
            "4": "$",
            "5": "%",
            "6": "^",
            "7": "&",
            "8": "*",
            "9": "(",
            "0": ")",
            "-": "_",
            "=": "+",
        }

        if key in qwerty_number_mappings:
            if is_shift_pressed:
                return qwerty_number_mappings[key]
            else:
                return key

        qwerty_punctuation_mappings = {
            ",": "<",
            ".": ">",
            "/": "?",
            ";": ":",
            "'": '"',
            "[": "{",
            "]": "}",
            "\\": "|",
            "`": "~",
        }

        if key in qwerty_punctuation_mappings:
            if is_shift_pressed:
                return qwerty_punctuation_mappings[key]
            else:
                return key

        return key
