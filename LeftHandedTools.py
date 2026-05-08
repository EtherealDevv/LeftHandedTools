import ctypes
import keyboard
import winsound
import time
import os
import sys
import json

# --- ADMIN PRIVILEGES CHECK ---
# Required to intercept keyboard events in most games
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# --- WINDOWS API SETUP ---
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
hwnd = kernel32.GetConsoleWindow()

# UI Colors and Positioning constants
L_GREEN, WHITE, RESET, HOME = '\033[92m', '\033[97m', '\033[0m', '\033[H'
CONFIG_FILE = "config.json"

def save_config(structured_mapping):
    """Saves the configuration with UTF-8 support for special characters (like 'ñ')."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False allows non-English characters to be saved as-is
        json.dump(structured_mapping, f, indent=4, ensure_ascii=False)

def load_config():
    """Loads the JSON config and flattens it for the remapping engine."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                flat_map = {}
                # Detects if it's the new structured format or the old flat one
                if any(isinstance(v, dict) for v in data.values()):
                    for section in data.values():
                        flat_map.update(section)
                else:
                    flat_map = data
                return flat_map
        except:
            return None
    return None

def clean_key_name(name):
    """Normalizes Spanish key names to standard English keyboard constants."""
    translations = {
        'ctrl derecha': 'right ctrl',
        'mayus': 'shift',
        'derecha shift': 'right shift',
        'espacio': 'space',
        'intro': 'enter',
        'retroceso': 'backspace'
    }
    return translations.get(name.lower(), name.lower())

def setup_wizard():
    """Initial configuration wizard organized by categories."""
    os.system('mode con: cols=65 lines=32')
    os.system('cls')
    print(f"{L_GREEN}╔══════════════════════════════════════════════════════════════╗")
    print(f"║               INITIAL CONFIGURATION - SYCHO                  ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{RESET}")
    print(f" [!] {CONFIG_FILE} not found. Creating configuration...")
    
    # Define mapping sections for the JSON file
    sections = {
        "MOVEMENT": [
            ('w', 'Move Forward (W)'), ('a', 'Move Left (A)'), 
            ('s', 'Move Backward (S)'), ('d', 'Move Right (D)'),
            ('space', 'Jump (Space)')
        ],
        "ACTIONS": [
            ('tab', 'Scoreboard/Inventory (Tab)'),
            ('left shift', 'Sprint (Shift)'), ('left ctrl', 'Crouch (Ctrl)'),
            ('q', 'Action Q (Drop)'), ('e', 'Action E (Interact)'),
            ('r', 'Reload (R)'), ('f', 'Flashlight (F)'),
            ('g', 'Grenade (G)'), ('t', 'Chat (T)'),
            ('z', 'Ability Z'), ('x', 'Ability X'), 
            ('c', 'Ability C'), ('v', 'Ability V')
        ],
        "INVENTORY": [
            ('1', 'Slot 1'), ('2', 'Slot 2'), ('3', 'Slot 3'),
            ('4', 'Slot 4'), ('5', 'Slot 5'), ('6', 'Slot 6')
        ]
    }
    
    structured_config = {}
    for section_name, targets in sections.items():
        print(f"\n --- {section_name} ---")
        section_map = {}
        for virtual, label in targets:
            print(f" > {WHITE}{label}:{RESET} ", end='', flush=True)
            while True:
                key_event = keyboard.read_event(suppress=True)
                if key_event.event_type == keyboard.KEY_DOWN:
                    real_key = clean_key_name(key_event.name)
                    display_name = "SPACEBAR" if real_key == " " else real_key.upper()
                    print(f"{L_GREEN}{display_name}{RESET}")
                    section_map[real_key] = virtual
                    time.sleep(0.15)
                    break
        structured_config[section_name] = section_map
            
    save_config(structured_config)
    print(f"\n{L_GREEN}[+] Config created successfully.{RESET}")
    time.sleep(1)
    
    # Flatten the map for immediate use
    flat_map = {}
    for s in structured_config.values(): flat_map.update(s)
    return flat_map

# --- CORE LOGIC INITIALIZATION ---
MIRROR_MAP = load_config() or setup_wizard()
os.system('mode con: cols=46 lines=16')

mouse_inverted, remap_active, console_visible = 1, False, True
cd = {'f1': 0, 'f2': 0, 'f3': 0}

def update_ui():
    """Refreshes the minimalist terminal interface."""
    sys.stdout.write(HOME)
    print(f"{L_GREEN}╔══════════════════════════════════════════╗")
    print(f"║          LEFT HANDED TOOLS v1.0          ║")
    print(f"║                 BY SYCHO                 ║")
    print(f"╚══════════════════════════════════════════╝{RESET}")
    print(f" {L_GREEN}>>{RESET} F1: INVERT MOUSE | F2: HIDE/SHOW")
    print(f" {L_GREEN}>>{RESET} F3: KEYS REMAP (ON/OFF)")
    print(f" {L_GREEN}------------------------------------------{RESET}")
    m_status = f"{L_GREEN}LEFTY " if mouse_inverted == 1 else f"{L_GREEN}RIGHTY"
    r_status = f"{L_GREEN}ACTIVE  " if remap_active else f"{WHITE}DISABLED"
    print(f" MOUSE MODE: {m_status}{RESET}")
    print(f" KEYS REMAP: {r_status}{RESET}")
    print(f" {L_GREEN}------------------------------------------{RESET}")
    # Dynamic counter for loaded keys
    print(f" {WHITE}Config: {len(MIRROR_MAP)} keys active.{RESET}")
    print(f" {L_GREEN}Press Ctrl+C to Exit & Reset Hardware.{RESET}")

def toggle_mouse():
    """Swaps primary/secondary mouse buttons via User32 API."""
    global mouse_inverted
    if time.time() - cd['f1'] < 0.4: return
    cd['f1'] = time.time()
    mouse_inverted = 1 - mouse_inverted
    user32.SwapMouseButton(mouse_inverted)
    winsound.Beep(1200 if mouse_inverted else 600, 100)
    if console_visible: update_ui()

def toggle_visibility():
    """Hides or shows the console window."""
    global console_visible
    if time.time() - cd['f2'] < 0.5: return
    cd['f2'] = time.time()
    user32.ShowWindow(hwnd, 0 if console_visible else 5)
    winsound.Beep(800 if console_visible else 1100, 100)
    console_visible = not console_visible

def toggle_remap():
    """Enables or disables keyboard remapping."""
    global remap_active
    if time.time() - cd['f3'] < 0.5: return
    cd['f3'] = time.time()
    remap_active = not remap_active
    if remap_active:
        for real, virtual in MIRROR_MAP.items():
            keyboard.remap_key(real, virtual)
        winsound.Beep(1000, 150)
    else:
        for real in MIRROR_MAP.keys():
            try: keyboard.unremap_key(real)
            except: pass
        winsound.Beep(400, 150)
    if console_visible: update_ui()

# --- STARTUP SEQUENCE ---
kernel32.SetConsoleTitleW("Left Handed Tools - By Sycho")
user32.SwapMouseButton(1)  # Default to Lefty mode on start
os.system('cls')
update_ui()

# Disable manual window resizing to keep the UI clean
style = user32.GetWindowLongW(hwnd, -16)
user32.SetWindowLongW(hwnd, -16, style & ~0x00040000 & ~0x00010000)

# Bind hotkeys
keyboard.add_hotkey('f1', toggle_mouse, suppress=True)
keyboard.add_hotkey('f2', toggle_visibility, suppress=True)
keyboard.add_hotkey('f3', toggle_remap, suppress=True)

try:
    keyboard.wait()
except KeyboardInterrupt:
    # Cleanup before exiting
    user32.SwapMouseButton(0)
    keyboard.unhook_all()
    user32.ShowWindow(hwnd, 5)
    sys.exit()