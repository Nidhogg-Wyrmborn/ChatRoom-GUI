import re
import tkinter as tk

class ANSIText(tk.Text):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        # Regex pattern matching standard 8-color and 256-color ANSI escape sequences
        self.ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')

    def ansi_to_hex(self, code_str):
        """
        Convert ANSI code sequence to Hex string.
        Custom/extend this method to match your specific ANSI converter logic.
        """
        codes = [int(x) for x in code_str.split(';') if x.isdigit()]
        
        # Standard foreground color codes (30-37)
        fg_map = {
            30: "#000000", 31: "#FF0000", 32: "#00FF00", 33: "#FFFF00",
            34: "#0000FF", 35: "#FF00FF", 36: "#00FFFF", 37: "#FFFFFF",
            90: "#808080", 91: "#FF6666", 92: "#66FF66", 93: "#FFFF66",
            94: "#6666FF", 95: "#FF66FF", 96: "#66FFFF", 97: "#FFFFFF"
        }

        for code in codes:
            if code in fg_map:
                return fg_map[code]
            elif code == 0:  # Reset
                return None
        return None

    def append_ansi_text(self, text):
        """Parses incoming ANSI text and inserts it with dynamic color tags."""
        current_color = None
        last_end = 0

        for match in self.ansi_pattern.finditer(text):
            # Insert text preceding the ANSI escape code
            clean_text = text[last_end:match.start()]
            if clean_text:
                self._insert_with_color(clean_text, current_color)

            # Extract color code and update active tag state
            ansi_code = match.group(1)
            if ansi_code == '0' or ansi_code == '':
                current_color = None
            else:
                new_color = self.ansi_to_hex(ansi_code)
                if new_color:
                    current_color = new_color

            last_end = match.end()

        # Insert any remaining text after the final escape code
        remaining_text = text[last_end:]
        if remaining_text:
            self._insert_with_color(remaining_text, current_color)

    def _insert_with_color(self, text, hex_color):
        if not hex_color:
            self.insert(tk.END, text)
            return

        # Use the hex string itself as a unique tag name
        tag_name = f"color_{hex_color.replace('#', '')}"
        
        # Dynamically create and configure the tag if it hasn't been created yet
        if tag_name not in self.tag_names():
            self.tag_configure(tag_name, foreground=hex_color)

        self.insert(tk.END, text, tag_name)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dynamic ANSI Tkinter Text")

    text_widget = ANSIText(root, bg="#1e1e1e", fg="#ffffff", font=("Consolas", 11))
    text_widget.pack(fill=tk.BOTH, expand=True)

    # Simulated incoming stream with red, green, and reset codes
    sample_stream = "\x1b[31m[ERROR]\x1b[0m System failure in \x1b[32mModule A\x1b[0m!\n"
    
    text_widget.append_ansi_text(sample_stream)

    root.mainloop()