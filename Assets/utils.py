import time
import re
import tkinter as tk
import sys
import subprocess
from tkinter import ttk

def listhas(lst, *args):
    lowered_list = {item.casefold() for item in lst}

    return any(arg.casefold() in lowered_list for arg in args)

class Timeout:
    def __init__(self, seconds):
        self.end_time = time.monotonic() + seconds

    def __call__(self):
        return time.monotonic() < self.end_time

def version_check(server_version: str, client_version: str) -> bool:
    # checks 2 versions against each other, assuming they each have the same number of digits
    # Release.Major.Minor
    try:
        primary_version = [int(i) for i in server_version.split('.')]
        secondary_version = [int(i) for i in client_version.split('.')]

        release = primary_version[0] == secondary_version[0]
        major = primary_version[1] == secondary_version[1]
        minor = primary_version[2] <= secondary_version[2]

        if release and major and minor:
            return True
        return False
    except:
        return False

def create_packet_template(command: str, allowed_values: list[str] = None) -> dict:
    """
    Creates a packet template structure for the given command.
    
    If `allowed_values` is provided, the template enforces [opt1|opt2] constraints.
    Otherwise, it accepts any arbitrary string input.
    """
    if allowed_values:
        choices_str = "|".join(allowed_values)
        pattern_value = f"[{choices_str}]"
    else:
        pattern_value = "string"

    raw_template = f"<|SET_{command.upper()}|>*{pattern_value}*<|END_SET|>"
    
    return {
        "command": command.lower(),
        "template": raw_template,
        "allowed_values": set(allowed_values) if allowed_values else None
    }

def create_packet_from_template(template_info: dict, value: str) -> str:
    template_str = template_info['template']
    allowed = template_info.get('allowed_values')

    if allowed is not None and value not in allowed:
        raise ValueError(
            f"Cannot build packet for '{template_info['command']}': "
            f"'{value}' is not in allowed values: {sorted(list(allowed))}"
        )

    packet = re.sub(r"\*.*?\*", value, template_str)

    return packet

def create_packet(packet: str, value: str) -> str:
    return re.sub(r"\*.*?\*", value, packet)

# Initialize command-to-packet dictionary
# command2packets = {
#     "color": create_packet_template("color", list(COLORS.keys())),
#     "uname": create_packet_template("uname")
# }


def parse_and_validate_packet(received_packet: str, command2packets: dict) -> dict:
    """
    Parses a received packet against key-value patterns and validates 
    it against the constraints defined in command2packets.
    
    Returns a dict with key/value if valid, or raises ValueError on criteria failure.
    """
    kv_pattern = r"<\|SET_(?P<key>\w+)\|>(?P<val>.*?)<\|END_SET\|>"
    match = re.fullmatch(kv_pattern, received_packet)
    
    if not match:
        raise ValueError(f"Packet syntax invalid: '{received_packet}'")
        
    cmd_key = match.group("key").lower()
    extracted_val = match.group("val")
    
    # Criteria 1: Check if command is registered
    if cmd_key not in command2packets:
        raise ValueError(f"Unknown command received: '{cmd_key}'")
        
    template_info = command2packets[cmd_key]
    allowed = template_info["allowed_values"]
    
    # Criteria 2: Check allowed value constraints
    if allowed is not None and extracted_val not in allowed:
        raise ValueError(
            f"Invalid value '{extracted_val}' for command '{cmd_key}'. "
            f"Allowed choices: {sorted(list(allowed))}"
        )
        
    return {
        "command": cmd_key,
        "value": extracted_val
    }

def check_allowed_values(packet: str) -> list[str] | None:
    # check what values are allowed for the particular packet

    kv_pattern = r"<\|SET_(?P<key>\w+)\|>(?P<val>.*?)<\|END_SET\|>"

    match = re.fullmatch(kv_pattern, packet)

    cmd_key = match.group("key")
    extracted_val = match.group('val')
    extracted_val = extracted_val.replace("*","")

    if any(v in extracted_val for v in ['|', '[', ']']):
        allowed_values = extracted_val.replace("[","").replace("]","").split('|')
    else:
        allowed_values = None

    return allowed_values

def ask_dropdown(parent, title, prompt, options):
    """
    Creates a modal pop-up dialog with a dropdown list.
    Returns the selected option string, or None if cancelled.
    """
    # Create a top-level window
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    
    # Make it modal (blocks interaction with the main window)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Position the dialog near the parent window
    dialog.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
    
    # Store the user's final selection
    result = {"value": None}
    
    # Add prompt label
    label = tk.Label(dialog, text=prompt, padx=10, pady=10)
    label.pack()
    
    # Add the dropdown (Combobox)
    # state="readonly" prevents the user from typing custom text
    dropdown = ttk.Combobox(dialog, values=options, state="readonly")
    if options:
        dropdown.current(0)  # Set default value to the first item
    dropdown.pack(padx=20, pady=10)
    
    # Define actions for buttons
    def on_ok():
        result["value"] = dropdown.get()
        dialog.destroy()
        
    def on_cancel():
        dialog.destroy()

    # Button layout container
    btn_frame = tk.Frame(dialog, pady=10)
    btn_frame.pack()
    
    ok_btn = tk.Button(btn_frame, text="OK", width=10, command=on_ok)
    ok_btn.pack(side=tk.LEFT, padx=5)
    
    cancel_btn = tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel)
    cancel_btn.pack(side=tk.LEFT, padx=5)
    
    # Wait until the dialog window is explicitly destroyed before returning execution
    dialog.wait_window()
    
    return result["value"]

def handleIE(IE):
    module = IE.name
    print(f"missing {module}, installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])
    except subprocess.CalledProcessError as CPE:
        print(f"Could not install {module}, check pypi!")
        return
    print(f"Installed {module} successfully!")
