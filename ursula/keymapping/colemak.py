from ursula.keymapping.keymap import Keymap


class Colemak(Keymap):
    def map(self, key: str, is_shift_pressed: bool) -> str:
        colemak_letter_mappings = {
            "q": "q",
            "w": "w",
            "e": "f",
            "r": "p",
            "t": "g",
            "y": "j",
            "u": "l",
            "i": "u",
            "o": "y",
            "p": ";",
            "a": "a",
            "s": "r",
            "d": "s",
            "f": "t",
            "g": "d",
            "h": "h",
            "j": "n",
            "k": "e",
            "l": "i",
            ";": "o",
            "z": "z",
            "x": "x",
            "c": "c",
            "v": "v",
            "b": "b",
            "n": "k",
            "m": "m",
        }

        if key.lower() in colemak_letter_mappings:
            mapped_key = colemak_letter_mappings[key.lower()]
            return mapped_key.upper() if is_shift_pressed else mapped_key

        colemak_number_mappings = {
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

        if key in colemak_number_mappings:
            if is_shift_pressed:
                return colemak_number_mappings[key]
            else:
                return key

        colemak_punctuation_mappings = {
            ",": "<",
            ".": ">",
            "/": "?",
            "'": '"',
            "[": "{",
            "]": "}",
            "\\": "|",
            "`": "~",
        }

        if key in colemak_punctuation_mappings:
            if is_shift_pressed:
                return colemak_punctuation_mappings[key]
            else:
                return key

        if key == ";":
            return ":" if is_shift_pressed else ";"

        return key
