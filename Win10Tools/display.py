import win32api
import win32con

class DisplayInfo:
    def __init__(self):
        # Récupérer tous les moniteurs au moment de la création
        self.monitors = win32api.EnumDisplayMonitors()

    def refresh(self):
        """Recharge la liste des moniteurs"""
        self.monitors = win32api.EnumDisplayMonitors()

    def get_monitor_count(self):
        """Retourne le nombre d'écrans connectés"""
        return len(self.monitors)

    def get_all_monitors_info(self, log=False):
        """Retourne les infos détaillées de tous les moniteurs"""
        monitors_info = []
        primary_index = self.get_primary_monitor()  # Calculer une seule fois

        for i, monitor in enumerate(self.monitors):
            # monitor est un tuple: (handle, hdc, rect)
            handle, hdc, rect = monitor

            # rect contient (left, top, right, bottom)
            left, top, right, bottom = rect

            primary = (i == primary_index)

            info = {
                'index': i,
                'handle': handle,
                'position': (left, top),
                'resolution': (right - left, bottom - top),
                'bounds': rect,
                'primary': primary
            }
            monitors_info.append(info)

            if log:
                # Afficher les infos de chaque moniteur
                print(f"Monitor {info['index']}: primary: {info['primary']}, handle: {info['handle']}, "
                      f"position: {info['position']}, resolution: {info['resolution']}, bounds: {info['bounds']}"
                  )

        return monitors_info

    def get_monitor_info(self, index: int):
        """Retourne les infos d’un moniteur spécifique"""
        monitors = self.get_all_monitors_info()
        if index < 0 or index >= len(monitors):
            return None
        return monitors[index]

    def get_primary_monitor(self, log=False):
        """Retourne l'index de l'écran principal"""
        for i, monitor in enumerate(self.monitors):
            handle, hdc, rect = monitor
            # L'écran principal a toujours la position (0, 0)
            if rect[0] == 0 and rect[1] == 0:
                if log:
                    print(f"Primary monitor index: {i}")
                return i
        return None

    def is_primary(self, index: int) -> bool:
        """Indique si un moniteur est principal"""
        return index == self.get_primary_monitor()


