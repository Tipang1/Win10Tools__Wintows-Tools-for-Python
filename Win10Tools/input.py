import ctypes
import time
import threading

class Mouse:
    """Contrôle de la souris"""

    @staticmethod
    def position(log=False):
        """Récupère la position actuelle de la souris"""
        try:
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            point = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))

            if log:
                print(f"Mouse position: ({point.x}, {point.y})")

            return (point.x, point.y)
        except Exception as e:
            if log:
                print(f"Error: {e}")
            return None

    @staticmethod
    def move(x, y=None, log=False):
        """Déplace la souris à une position (x, y) ou tuple (x, y)"""
        try:
            # Accepter tuple
            if isinstance(x, tuple):
                y = x[1]
                x = x[0]

            ctypes.windll.user32.SetCursorPos(x, y)

            if log:
                print(f"Mouse moved to ({x}, {y})")

            return True
        except Exception as e:
            if log:
                print(f"Error: {e}")
            return False

    @staticmethod
    def click(button="left", duration=0.1, x=None, y=None, blocking=True, log=False):
        if x is not None:
            Mouse.move(x, y, log=log)

        """Simule un clic souris"""
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        MOUSEEVENTF_MIDDLEDOWN = 0x0020
        MOUSEEVENTF_MIDDLEUP = 0x0040

        events = {
            "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP)
        }

        def _click():
            try:
                if button not in events:
                    if log:
                        print(f"Invalid button: {button}")
                    return False

                down, up = events[button]

                # DOWN
                ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)

                try:
                    time.sleep(duration)
                finally:
                    # TOUJOURS faire le UP, même si ça plante
                    ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

                if log:
                    print(f"{button.capitalize()} click performed ({duration}s)")

                return True
            except Exception as e:
                if log:
                    print(f"Error: {e}")
                return False

        if blocking:
            return _click()
        else:
            thread = threading.Thread(target=_click, daemon=True)
            thread.start()
            return thread


class Keyboard:
    """Contrôle du clavier"""

    @staticmethod
    def press(key, duration=0.1, log=False):
        """Appuie sur une touche"""
        try:
            import ctypes
            from ctypes import wintypes

            VK_CODES = {
                'enter': 0x0D, 'space': 0x20, 'backspace': 0x08,
                'tab': 0x09, 'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
                'escape': 0x1B, 'delete': 0x2E,
                'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,

                # Lettres
                'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
                'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
                'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
                'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
                'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,

                # Numpad (pavé numérique)
                'num0': 0x60, 'num1': 0x61, 'num2': 0x62, 'num3': 0x63, 'num4': 0x64,
                'num5': 0x65, 'num6': 0x66, 'num7': 0x67, 'num8': 0x68, 'num9': 0x69,

                # Touches AZERTY belge (rangée chiffres = caractères spéciaux)
                '&': 0x31,  # Touche 1 (produit &)
                'é': 0x32,  # Touche 2 (produit é)
                '"': 0x33,  # Touche 3 (produit ")
                "'": 0x34,  # Touche 4 (produit ')
                '(': 0x35,  # Touche 5 (produit ()
                '§': 0x36,  # Touche 6 (produit §)
                'è': 0x37,  # Touche 7 (produit è)
                '!': 0x38,  # Touche 8 (produit !)
                'ç': 0x39,  # Touche 9 (produit ç)
                'à': 0x30,  # Touche 0 (produit à)
            }


            vk_code = None
            if isinstance(key, int):
                vk_code = key
            else:
                key_lower = key.lower()
                if key_lower not in VK_CODES:
                    if log:
                        print(f"Unknown key: {key}")
                    return False

                vk_code = VK_CODES[key_lower]

            KEYEVENTF_KEYUP = 0x0002

            # Press down
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)

            try:
                time.sleep(duration)
            finally:
                # Release
                ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

            if log:
                print(f"Key pressed: {key}")

            return True
        except Exception as e:
            if log:
                print(f"Error: {e}")
            return False

    @staticmethod
    def write(text, delay=0.05, log=False):
        """Tape du texte"""
        try:
            for char in text:
                if char == ' ':
                    Keyboard.press('space', duration=0.05, log=log)
                    continue
                if char == '\n':
                    Keyboard.press('enter', duration=0.05, log=log)
                    continue
                elif char.lower() in 'abcdefghijklmnopqrstuvwxyz&é"\'(§è!çà':
                    Keyboard.press(char, duration=0.05, log=log)
                    continue
                elif char.isdigit():
                    Keyboard.press(f'num{char}', duration=0.05, log=log)
                    continue
                else:
                    # Caractères spéciaux pas supportés pour l'instant
                    pass
                time.sleep(delay)

            if log:
                print(f"Text written: {text}")

            return True
        except Exception as e:
            if log:
                print(f"Error: {e}")
            return False

    @staticmethod
    def hotkey(*keys, log=False):
        """Simule une combinaison de touches (ex: ctrl+c)"""
        try:
            # Appuyer sur toutes les touches
            for key in keys:
                Keyboard.press(key, duration=0)

            time.sleep(0.1)

            if log:
                print(f"Hotkey pressed: {'+'.join(keys)}")

            return True
        except Exception as e:
            if log:
                print(f"Error: {e}")
            return False
