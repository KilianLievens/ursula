import tkinter as tk
import keyboard
import os
import logging
import time
import sys

from abc import abstractmethod
from PIL import Image, ImageDraw, ImageFont, ImageTk
from ursula.keymapping.azerty import Azerty
from ursula.keymapping.keymap import Keymap
from ursula.keymapping.factory import KeymapFactory
from ursula.lib.epd import EPD

# TODO KILIAN: split file
# Set up logging
logging.basicConfig(level=logging.DEBUG)


# Display Interface
class DisplayInterface:
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
    def get_dimensions(self) -> tuple[int, int]:
        """Return width and height of the display"""
        pass

    @abstractmethod
    def sleep(self):
        """Put the display to sleep mode if applicable"""
        pass

    @abstractmethod
    def get_sleeping(self) -> bool:
        """Check if the display is asleep"""
        pass

    @abstractmethod
    def close(self):
        """Clean up resources"""
        pass


# E-Ink Display Implementation
class EInkDisplay(DisplayInterface):
    def __init__(self):
        try:

            self.epd = EPD()
            self.width = self.epd.width
            self.height = self.epd.height
            self.partial_refresh_counter = 0
            self.sleeping = True  # Should be init() first
        except ImportError:
            logging.error("E-Ink display module not found.")
            raise

    def init(self):
        logging.debug("Initializing E-Ink display")
        self.epd.init()
        self.epd.Clear()
        self.epd.init_part()
        self.sleeping = False

    def clear(self):
        logging.debug("Clearing E-Ink display")

        assert not self.sleeping, "Display is asleep. Cannot clear image."

        self.epd.Clear()

    def display(self, image):
        assert not self.sleeping, "Display is asleep. Cannot display image."

        logging.debug("Displaying image on E-Ink display")
        buffer = self.epd.getbuffer(image)
        if self.partial_refresh_counter > 30:
            # Full refresh
            self.epd.display(buffer)
            self.partial_refresh_counter = 0
            return

        # TODO KILIAN: try again to do partial updates over only part of the screen
        self.epd.display_Partial(buffer, 0, 0, self.width, self.height)
        self.partial_refresh_counter += 1

    def get_dimensions(self):
        return (self.width, self.height)

    def sleep(self):
        if self.sleeping:
            return
        self.epd.sleep()
        self.sleeping = True

    def get_sleeping(self):
        """Check if the display is asleep"""
        return self.sleeping

    def close(self):
        if self.sleeping:
            logging.debug("Display is already asleep. No need to close.")
            return

        self.epd.init()
        self.epd.Clear()
        self.sleep()


# Tkinter Simulator Implementation
class TkinterDisplay(DisplayInterface):
    def __init__(self, width=800, height=480, scale_factor=2):
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

        self.canvas = tk.Canvas(
            self.root,
            width=self.physical_width,
            height=self.physical_height,
            bg="#f0f0f0",
            highlightthickness=0,
        )
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
            self.physical_width // 2,
            self.physical_height // 2,
            anchor=tk.CENTER,
            image=self.tk_image,
        )

        # Simulate a delay for the display update
        time.sleep(0.5)
        # Update the display
        self.root.update()

    def get_dimensions(self):
        return (self.logical_width, self.logical_height)

    def sleep(self):
        logging.debug("Tkinter simulator doesn't require sleep mode")
        pass

    def get_sleeping(self):
        """Check if the display is asleep"""
        return False

    def close(self):
        logging.debug("Closing Tkinter simulator")
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

    # TODO KILIAN: a run in the interface?
    def mainloop(self):
        """Start the Tkinter main loop"""
        if self.root:
            self.root.mainloop()


# Typewriter Application
class Typewriter:
    def __init__(self, display, simulation: bool, keymap: Keymap):
        self.display = display
        self.width, self.height = display.get_dimensions()
        self.lines = [""]
        self.font_size = 32
        self.line_height = self.font_size + 8

        self.simulation = simulation
        self.last_action_time = time.time()
        self.keymap = keymap

        # Default save file name
        self.save_file = "typewriter_content.txt"

        # Batched display update settings
        self.display_update_delay = 0.05
        self.chars_since_update = 0
        self.last_keypress_time = 0

        # Load font
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.font = ImageFont.truetype(
            os.path.join(dir_path, "lib", "font.ttc"), self.font_size
        )

        # Try to load a fancy font for splash screen, fall back to regular font if not available
        try:
            self.splash_font = ImageFont.truetype(
                os.path.join(dir_path, "lib", "font.ttc"), 96
            )
            # Alternatively, you could try to use a different font file if not available:
            # self.splash_font = ImageFont.truetype("arial.ttf", 96)
        except IOError:
            logging.warning(
                "Fancy font not found. Using regular font for splash screen."
            )
            self.splash_font = self.font

        # Create initial image
        self.image = Image.new("1", (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)

        # Flag to control keyboard listener
        self.running = True

        # Initialize the display
        self.display.init()

        # Load existing content before showing splash screen
        self.load_content()

        # Show splash screen
        self.show_splash_screen()

    def save_content(self):
        """Save current lines to a file"""
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                content = "\n".join(self.lines)
                f.write(content)
            logging.info(f"Content saved to {self.save_file}")
        except Exception as e:
            logging.error(f"Failed to save content: {e}")

    def load_content(self):
        """Load content from file if it exists"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        self.lines = content.split("\n")
                        # Ensure we have at least one line
                        if not self.lines:
                            self.lines = [""]
                        logging.info(f"Content loaded from {self.save_file}")
                    else:
                        self.lines = [""]
            else:
                logging.info(f"No existing save file found at {self.save_file}")
        except Exception as e:
            logging.error(f"Failed to load content: {e}")
            self.lines = [""]

    def show_splash_screen(self):
        """Display a splash screen with 'Ursula' text"""
        logging.debug("Showing splash screen")

        # Clear the image and create a new blank canvas
        splash_image = Image.new(
            "1", (self.width, self.height), 255
        )  # White background
        splash_draw = ImageDraw.Draw(splash_image)

        # Text to display
        text = "Ursula"

        # Calculate text dimensions to center it
        text_width = splash_draw.textlength(text, font=self.splash_font)
        text_height = self.splash_font.size

        # Draw text centered on the screen
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        # Add decorative elements (simple lines)
        line_length = text_width + 80
        line_y_above = y - 40
        line_y_below = y + text_height + 20

        # Draw horizontal lines above and below the text
        splash_draw.line(
            [
                (self.width - line_length) // 2,
                line_y_above,
                (self.width + line_length) // 2,
                line_y_above,
            ],
            fill=0,
            width=3,
        )
        splash_draw.line(
            [
                (self.width - line_length) // 2,
                line_y_below,
                (self.width + line_length) // 2,
                line_y_below,
            ],
            fill=0,
            width=3,
        )

        # Draw the text
        splash_draw.text((x, y), text, font=self.splash_font, fill=0)  # Black text

        # Add a subtitle
        subtitle = "Typewriter"
        sub_subtitle = "For Hans, by Kels with love."
        subtitle_font = ImageFont.truetype(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "lib", "font.ttc"
            ),
            24,
        )
        sub_subtitle_font = ImageFont.truetype(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "lib", "font.ttc"
            ),
            18,
        )
        subtitle_width = splash_draw.textlength(subtitle, font=subtitle_font)
        sub_subtitle_width = splash_draw.textlength(
            sub_subtitle, font=sub_subtitle_font
        )
        subtitle_x = (self.width - subtitle_width) // 2
        sub_subtitle_x = (self.width - sub_subtitle_width) // 2
        subtitle_offset = 40
        subtitle_y = y + text_height + subtitle_offset
        splash_draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill=0)
        splash_draw.text(
            (sub_subtitle_x, subtitle_y + subtitle_offset),
            sub_subtitle,
            font=sub_subtitle_font,
            fill=0,
        )

        # Display the splash screen
        self.display.display(splash_image)

        # Wait for a moment before continuing
        time.sleep(4)
        self.display.clear()

    def setup_keyboard_listener(self):
        """Set up global keyboard event listener"""
        keyboard.on_press(self.handle_keypress)

    def sleep_after_inactivity(self):
        """Put the display to sleep after a period of inactivity"""
        # Put the display to sleep if it has been inactive for a minute
        if not self.display.get_sleeping() and time.time() - self.last_action_time > 60:
            logging.info("Putting display to sleep due to inactivity")
            self.display.sleep()
            return

    def should_update_display(self):
        """Check if display should be updated based on time"""
        current_time = time.time()
        time_since_last_key = current_time - self.last_keypress_time

        # Move chars since update?
        return (
            self.chars_since_update > 0
            and time_since_last_key >= self.display_update_delay
        )

    def trigger_display_update(self, force_immediate=False):
        """Trigger a display update either immediately or check if batched update needed"""
        current_time = time.time()
        self.last_keypress_time = current_time

        if force_immediate:
            self.chars_since_update = 0
            self.update_display()
        else:
            self.chars_since_update += 1

    def handle_keypress(self, event):
        """Process keyboard events from the keyboard module"""
        if not self.running:
            return

        if self.display.get_sleeping():
            # If the display is asleep, wake it up
            self.display.init()

        # Update the last action time
        self.last_action_time = time.time()

        # Get the key name
        key = self.keymap.map(event.name, keyboard.is_pressed("shift"))

        # Handle Ctrl+S for saving
        if key == "s" and keyboard.is_pressed("ctrl"):
            self.save_content()
            return

        # Handle Ctrl+P for power off
        if key == "p" and keyboard.is_pressed("ctrl"):
            self.power_off()
            return

        # Handle Ctrl+W for deleting a full word
        if key == "w" and keyboard.is_pressed("ctrl"):
            # Remove the last word from the current line
            if len(self.lines[-1]) > 0:
                parts = self.lines[-1].rsplit(" ", 1)
                if len(parts) > 1:
                    self.lines[-1] = parts[0]
                else:
                    self.lines[-1] = ""
            self.trigger_display_update()
            return

        # Process different keys
        if key == "enter":
            # Move to a new line when Enter/Return is pressed
            self.lines.append("")
            self.trigger_display_update(force_immediate=True)
            return

        if key == "backspace":
            # Nothing to remove
            if len(self.lines) == 1 and len(self.lines[-1]) == 0:
                return

            # Remove a letter
            if len(self.lines[-1]) > 0:
                self.lines[-1] = self.lines[-1][:-1]
                self.trigger_display_update()
                return

            # Go to previous line if at start of current line
            self.lines.pop()
            self.trigger_display_update(force_immediate=True)
            return

        # TODO KILIAN: technically you could add endless space at the end of a line without noticing.
        if key == "space":
            # Add space
            self.lines[-1] += " "
            self.trigger_display_update()
            return

        if len(key) > 1:
            # Ignore other special keys (like Ctrl, Alt, etc.)
            return

        # TODO KILIAN: parameterize the padding
        # 20 pixels: padding for the left side + right side
        if self.get_text_width(self.lines[-1]) >= self.width - 20:
            # TODO KILIAN: move to function
            # Move to a new line if the current line exceeds the width
            parts = self.lines[-1].rsplit(" ", 1)
            if len(parts) > 1:
                # Move the last part to a new line
                # Technically, when backspacing we could reverse this operation if relevant.
                # Lets not for now.
                self.lines[-1] = parts[0]
                self.lines.append(parts[1])
            else:
                self.lines.append("")

        self.lines[-1] += key
        self.trigger_display_update()

    def get_text_width(self, text):
        """Get the width of text in pixels"""
        return self.draw.textlength(text, font=self.font)

    def update_display(self):
        """Update the display with the current text"""
        # Clear the image
        self.image = Image.new("1", (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)

        # TODO
        # Local copy to avoid concurrency issues with the hook
        lines_snapshot = list(self.lines)

        # Calculate how many lines can fit on screen
        visible_lines = min(len(lines_snapshot), self.height // self.line_height)

        # Calculate which lines to display
        if len(lines_snapshot) <= visible_lines:
            start_line = 0
        else:
            start_line = len(lines_snapshot) - visible_lines

        # Draw visible lines
        for i in range(visible_lines):
            line_index = start_line + i
            y_position = self.height - (visible_lines - i) * self.line_height
            text = lines_snapshot[line_index]
            if i == visible_lines - 1:
                text = text + "_"  # Add cursor to the last line
            self.draw.text((10, y_position), text, font=self.font, fill=0)

        # Display the updated image
        self.display.display(self.image)

    def check_pending_updates(self):
        """Check and execute any pending display updates"""
        if self.should_update_display():
            self.chars_since_update = 0
            self.update_display()

    def run(self):
        """Run the typewriter application"""
        self.setup_keyboard_listener()
        self.update_display()

        # TODO KILIAN
        # For TkinterDisplay, we need to keep the mainloop running
        if isinstance(self.display, TkinterDisplay):
            # For Tkinter, we need to periodically check for pending updates
            def check_updates():
                if self.running:
                    self.check_pending_updates()
                    self.display.root.after(100, check_updates)  # Check every 100ms

            check_updates()  # Start the update checking
            self.display.mainloop()
        else:
            while self.running:
                # Check if we need to update display for pending characters
                self.check_pending_updates()
                self.sleep_after_inactivity()
                time.sleep(0.05)

    def power_off(self):
        """Save content, close application, and power off the machine"""
        logging.info("Power off requested (Ctrl+P)")

        # Save content before powering off
        self.save_content()

        # Stop the application
        self.display.close()

        time.sleep(4)

        if self.simulation:
            logging.info("Exiting simulation mode")
            os._exit(0)
            return

        os.system("sudo shutdown -h now")


def main(use_simulator: bool, keymap: Keymap):
    if use_simulator:
        logging.info("Using Tkinter simulator")
        display = TkinterDisplay(800, 480)
    else:
        logging.info("Using E-Ink display")
        display = EInkDisplay()

    typewriter = Typewriter(display, use_simulator, keymap)
    typewriter.run()


if __name__ == "__main__":
    import sys

    use_simulator = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "eink":
        use_simulator = False

    keymap = Azerty()
    if len(sys.argv) > 2:
        raw_keymap = sys.argv[2].lower()
        keymap = KeymapFactory.create(raw_keymap)

    main(use_simulator, keymap)
