import tkinter as tk
import keyboard
import os
import logging
import time
from abc import abstractmethod
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Abstract Display Interface
class DisplayInterface():
    @abstractmethod
    def init(self):
        """Initialize the display"""
        pass

    @abstractmethod
    def clear(self):
        """Clear the display"""
        pass

    @abstractmethod
    def display(self, image):
        """Display an image on the screen"""
        pass

    @abstractmethod
    def get_dimensions(self):
        """Return width and height of the display"""
        pass

    @abstractmethod
    def sleep(self):
        """Put the display to sleep mode if applicable"""
        pass

    @abstractmethod
    def close(self):
        """Clean up resources"""
        pass

# E-Ink Display Implementation
class EInkDisplay(DisplayInterface):
    def __init__(self):
        try:
            from ursula.lib.epd import EPD, epdconfig
            self.epd = EPD()
            self.epdconfig = epdconfig
            self.width = self.epd.width
            self.height = self.epd.height
        except ImportError:
            logging.error("E-Ink display module not found. Make sure 'ursula.lib.epd' is available.")
            raise

    def init(self):
        logging.debug("Initializing E-Ink display")
        self.epd.init()

    def init_partial(self):
        """Initialize for partial updates"""
        self.epd.init_part()

    def clear(self):
        logging.debug("Clearing E-Ink display")
        self.epd.Clear()

    def display(self, image):
        logging.debug("Displaying image on E-Ink display")
        self.epd.display(self.epd.getbuffer(image))

    def display_partial(self, image, x, y, w, h):
        """Partial update of the display"""
        self.epd.display_Partial(self.epd.getbuffer(image), x, y, w, h)

    def get_dimensions(self):
        return (self.width, self.height)

    def sleep(self):
        logging.debug("Putting E-Ink display to sleep")
        self.epd.sleep()

    def close(self):
        logging.debug("Closing E-Ink display")
        self.epdconfig.module_exit(cleanup=True)

# Tkinter Simulator Implementation
class TkinterDisplay(DisplayInterface):
    def __init__(self, width=800, height=480, scale_factor=3):
        self.logical_width = width
        self.logical_height = height
        self.scale_factor = scale_factor

        # Calculate the actual window dimensions based on scale factor
        self.physical_width = int(width * scale_factor)
        self.physical_height = int(height * scale_factor)

        self.root = None
        self.canvas = None
        self.tk_image = None
        self.image_on_canvas = None

    def init(self):
        logging.debug("Initializing Tkinter display simulator")
        self.root = tk.Tk()
        self.root.title(f"E-Ink Display Simulator (Scale: {self.scale_factor}x)")
        self.root.geometry(f"{self.physical_width}x{self.physical_height}")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        self.canvas = tk.Canvas(self.root, width=self.physical_width, height=self.physical_height,
                               bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def clear(self):
        logging.debug("Clearing Tkinter display simulator")
        if self.canvas:
            self.canvas.delete("all")
            self.canvas.configure(bg="#f0f0f0")
            self.root.update()

    def display(self, image):
        logging.debug("Displaying image on Tkinter simulator")
        if not self.root:
            self.init()

        # Convert the PIL image to a Tkinter PhotoImage
        scaled_image = image.resize((self.physical_width, self.physical_height))
        self.tk_image = ImageTk.PhotoImage(scaled_image)

        # If there's already an image on the canvas, delete it
        if self.image_on_canvas:
            self.canvas.delete(self.image_on_canvas)

        # Create a new image on the canvas
        self.image_on_canvas = self.canvas.create_image(
            self.physical_width // 2, self.physical_height // 2, anchor=tk.CENTER, image=self.tk_image
        )

        # Update the display
        self.root.update()

    def get_dimensions(self):
        return (self.logical_width, self.logical_height)

    def sleep(self):
        logging.debug("Tkinter simulator doesn't require sleep mode")
        pass

    def close(self):
        logging.debug("Closing Tkinter simulator")
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

    def update(self):
        """Process Tkinter events"""
        if self.root:
            self.root.update()

    def mainloop(self):
        """Start the Tkinter main loop"""
        if self.root:
            self.root.mainloop()

# Typewriter Application
class Typewriter:
    def __init__(self, display):
        self.display = display
        self.width, self.height = display.get_dimensions()
        self.lines = [""]
        self.font_size = 32
        self.line_height = self.font_size + 8

        # Load font
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.font = ImageFont.truetype(os.path.join(dir_path, "lib", "font.ttc"), self.font_size)

        # Create initial image
        self.image = Image.new("1", (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)

        # Flag to control keyboard listener
        self.running = True

        # Initialize the display
        self.display.init()
        self.display.clear()

    def setup_keyboard_listener(self):
        """Set up global keyboard event listener"""
        keyboard.on_press(self.handle_keypress)

    def handle_keypress(self, event):
        """Process keyboard events from the keyboard module"""
        if not self.running:
            return

        # Get the key name
        key = event.name

        # Process different keys
        if key == 'enter':
            # Move to a new line when Enter/Return is pressed
            self.lines.append("")
            self.update_display()
            return

        if key == 'backspace':
            # Nothing to remove
            if len(self.lines) == 1 and len(self.lines[-1]) == 0:
                return

            # Remove a letter
            if len(self.lines[-1]) > 0:
                self.lines[-1] = self.lines[-1][:-1]
                self.update_display()
                return

            # Go to previous line if at start of current line
            self.lines.pop()
            self.update_display()
            return

        if len(key) > 1:
            # Ignore other special keys (like Ctrl, Alt, etc.)
            return

        # TODO KILIAN: parameterize the padding
        # 20 pixels: padding for the left side + right side
        if self.get_text_width(self.lines[-1]) >= self.width - 20:
            # Move to a new line if the current line exceeds the width
            self.lines.append("")

        if key == 'space':
            # Add space
            self.lines[-1] += ' '
            self.update_display()
            return

        if key.isalnum():
            # Check for shift key to handle uppercase
            if keyboard.is_pressed('shift'):
                key = key.upper()

            self.lines[-1] += key
            self.update_display()
            return

        # TODO KILIAN: move
        shift_map = {
            '.': '>',
            ',': '<',
            ';': ':',
            '/': '?',
            '\\': '|',
            '-': '_',
            '=': '+',
            '[': '{',
            ']': '}',
            "'": '"',
            '`': '~'
        }
        if shift_map.get(key) is not None:
            # Apply shift key modifications if needed
            char = shift_map.get(key) if keyboard.is_pressed('shift') else key
            self.lines[-1] += char
            self.update_display()
            return

        self.lines[-1] += key
        self.update_display()

    def get_text_width(self, text):
        """Get the width of text in pixels"""
        return self.draw.textlength(text, font=self.font)

    def update_display(self):
        """Update the display with the current text"""
        # Clear the image
        self.image = Image.new("1", (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)

        # Calculate how many lines can fit on screen
        visible_lines = min(len(self.lines), self.height // self.line_height)

        # Calculate which lines to display
        if len(self.lines) <= visible_lines:
            start_line = 0
        else:
            start_line = len(self.lines) - visible_lines

        # Draw visible lines
        for i in range(visible_lines):
            line_index = start_line + i
            y_position = self.height - (visible_lines - i) * self.line_height
            self.draw.text((10, y_position), self.lines[line_index], font=self.font, fill=0)

        # Display the updated image
        self.display.display(self.image)

    def run(self):
        """Run the typewriter application"""
        self.setup_keyboard_listener()
        self.update_display()

        # For TkinterDisplay, we need to keep the mainloop running
        if isinstance(self.display, TkinterDisplay):
            try:
                self.display.mainloop()
            except KeyboardInterrupt:
                self.stop()
        else:
            # For EInkDisplay, we need to keep the script running
            try:
                while self.running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the typewriter application"""
        self.running = False
        keyboard.unhook_all()
        self.display.close()

# Main function - choose the display based on environment or command line argument
def main(use_simulator=True):
    if use_simulator:
        logging.info("Using Tkinter simulator")
        display = TkinterDisplay(800, 480)
    else:
        logging.info("Using E-Ink display")
        try:
            display = EInkDisplay()
        except ImportError:
            logging.warning("E-Ink display module not found, falling back to simulator")
            display = TkinterDisplay(800, 480)

    typewriter = Typewriter(display)
    typewriter.run()

if __name__ == "__main__":
    import sys
    # Use simulator by default, unless "eink" is passed as an argument
    use_simulator = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "eink":
        use_simulator = False

    main(use_simulator)
