from abc import abstractmethod

class Keymap:
    @abstractmethod
    def map(self, key: str, is_shift_pressed: bool) -> str:
        """Get the key associated with an action."""
        pass
