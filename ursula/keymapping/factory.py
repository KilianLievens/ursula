from ursula.keymapping.azerty import Azerty
from ursula.keymapping.colemak import Colemak
from ursula.keymapping.keymap import Keymap
from ursula.keymapping.qwerty import Qwerty

class KeymapFactory:
    @staticmethod
    def create(layout: str) -> Keymap:
        """Create a keymap based on the specified layout."""
        match layout.lower():
            case "azerty":
                return Azerty()
            case "qwerty":
                return Qwerty()
            case "colemak":
                return Colemak()
            case _:
                raise ValueError(f"Unsupported keymap layout: {layout}")
