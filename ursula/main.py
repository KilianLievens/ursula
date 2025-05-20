import tkinter as tk
import keyboard
import os
import logging
import time
from abc import abstractmethod
from PIL import Image, ImageDraw, ImageFont, ImageTk

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
    def close(self):
        """Clean up resources"""
        pass


# E-Ink Display Implementation
class EInkDisplay(DisplayInterface):
    def __init__(self):
        try:
            from ursula.lib.epd import EPD

            self.epd = EPD()
            self.width = self.epd.width
            self.height = self.epd.height
            self.partial_refresh_counter = 0
        except ImportError:
            logging.error("E-Ink display module not found.")
            raise

    def init(self):
        logging.debug("Initializing E-Ink display")
        self.epd.init_part()

    def clear(self):
        logging.debug("Clearing E-Ink display")
        self.epd.Clear()

    def display(self, image):
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
        logging.debug("Putting E-Ink display to sleep")
        self.epd.sleep()

    def close(self):
        self.sleep()


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

    # TODO KILIAN: a run in the interface?
    def mainloop(self):
        """Start the Tkinter main loop"""
        if self.root:
            self.root.mainloop()


# Typewriter Application
class Typewriter:
    def __init__(self, display, simulation=True):
        self.display = display
        self.width, self.height = display.get_dimensions()
        self.lines = [""]
        self.font_size = 32
        self.line_height = self.font_size + 8

        self.simulation = simulation

        # Default save file name
        self.save_file = "typewriter_content.txt"

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
            # Alternatively, you could try to use a different font file if available:
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
        self.display.clear()

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
        time.sleep(3)

    def setup_keyboard_listener(self):
        """Set up global keyboard event listener"""
        keyboard.on_press(self.handle_keypress)

    def handle_keypress(self, event):
        """Process keyboard events from the keyboard module"""
        if not self.running:
            return

        # Get the key name
        key = event.name

        # Handle Ctrl+S for saving
        if key == "s" and keyboard.is_pressed("ctrl"):
            self.save_content()
            return

        # Handle Ctrl+P for power off
        if key == "p" and keyboard.is_pressed("ctrl"):
            self.power_off()
            return

        # Process different keys
        if key == "enter":
            # Move to a new line when Enter/Return is pressed
            self.lines.append("")
            self.update_display()
            return

        if key == "backspace":
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

        # TODO KILIAN: technically you could add endless space at the end of a line without noticing.
        if key == "space":
            # Add space
            self.lines[-1] += " "
            self.update_display()
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

        if key.isalnum():
            # Check for shift key to handle uppercase
            if keyboard.is_pressed("shift"):
                key = key.upper()

            self.lines[-1] += key
            self.update_display()
            return

        # TODO KILIAN: move
        shift_map = {
            ".": ">",
            ",": "<",
            ";": ":",
            "/": "?",
            "\\": "|",
            "-": "_",
            "=": "+",
            "[": "{",
            "]": "}",
            "'": '"',
            "`": "~",
        }
        if shift_map.get(key) is not None:
            # Apply shift key modifications if needed
            char = shift_map.get(key) if keyboard.is_pressed("shift") else key
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
            self.draw.text(
                (10, y_position), self.lines[line_index], font=self.font, fill=0
            )

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

    def power_off(self):
        """Save content, close application, and power off the machine"""
        logging.info("Power off requested (Ctrl+P)")

        # Save content before powering off
        self.save_content()

        # Show a brief power off message
        self.show_power_off_screen()

        # Stop the application
        self.running = False
        keyboard.unhook_all()
        self.display.close()

        if self.simulation:
            logging.info("Exiting simulation mode")
            os._exit(0)

        try:
            import subprocess
            import sys

            subprocess.run(["poweroff"], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to power off: {e}")
            logging.info(
                "Note: You may need to run this script with appropriate privileges for power off"
            )
            # Just quit the application if power off fails
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during power off: {e}")
            sys.exit(1)


# Main function - choose the display based on environment or command line argument
def main(use_simulator=True):
    if use_simulator:
        logging.info("Using Tkinter simulator")
        display = TkinterDisplay(800, 480)
    else:
        logging.info("Using E-Ink display")
        display = EInkDisplay()

    typewriter = Typewriter(display, use_simulator)
    typewriter.run()


if __name__ == "__main__":
    import sys

    # Use simulator by default, unless "eink" is passed as an argument
    use_simulator = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "eink":
        use_simulator = False

    main(use_simulator)
