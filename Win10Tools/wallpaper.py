from pathlib import Path
import ctypes
import winreg

from comtypes import GUID, CoCreateInstance, COMMETHOD, HRESULT
from ctypes import POINTER, c_wchar_p, c_uint
from comtypes import IUnknown


##############################################################
#                      CLASSES COMMUNES                      #
##############################################################

# Définir l'interface IDesktopWallpaper
class IDesktopWallpaper(IUnknown):
    _iid_ = GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")

    _methods_ = [
        COMMETHOD([], HRESULT, "SetWallpaper",
                  (['in'], c_wchar_p, "monitorID"),
                  (['in'], c_wchar_p, "wallpaper")),

        COMMETHOD([], HRESULT, "GetWallpaper",
                  (['in'], c_wchar_p, "monitorID"),
                  (['out'], POINTER(c_wchar_p), "wallpaper")),

        COMMETHOD([], HRESULT, "GetMonitorDevicePathAt",
                  (['in'], c_uint, "monitorIndex"),
                  (['out'], POINTER(c_wchar_p), "monitorID")),

        COMMETHOD([], HRESULT, "GetMonitorDevicePathCount",
                  (['out'], POINTER(c_uint), "count")),
    ]


##############################################################
#                      CLASSE WALLPAPER                      #
##############################################################
class WallpaperManager:
    # Constantes pour l'API Windows
    SPI_SETDESKWALLPAPER = 0x0014  # Code qui dit "je veux changer le fond d'écran"
    SPIF_UPDATEINIFILE = 0x0001  # Sauvegarder le changement
    SPIF_SENDCHANGE = 0x0002  # Notifier le système du changement

    @staticmethod
    def set_global_wallpaper(image_path, log=False):
        """Change le fond d'écran de tous les moniteurs"""
        # Vérifier que le fichier existe
        path = Path(image_path)
        if not path.exists():
            if log:
                print(f"Error: Image not found at {image_path}")
            return False

        # Convertir en chemin absolu
        abs_path = str(path.absolute())

        # Appeler l'API Windows
        result = ctypes.windll.user32.SystemParametersInfoW(
            WallpaperManager.SPI_SETDESKWALLPAPER,
            0,
            abs_path,
            WallpaperManager.SPIF_UPDATEINIFILE | WallpaperManager.SPIF_SENDCHANGE
        )

        if log:
            if result:
                print(f"Wallpaper changed successfully to: {abs_path}")
            else:
                print("Failed to change wallpaper")

        return bool(result)

    @staticmethod
    def set_wallpaper_per_monitor(monitor_configs, display_info, log=False):
        """
        Change le fond d'écran de moniteurs spécifiques

        Args:
            monitor_configs: Liste de tuples (monitor_index, image_path)
            display_info: Instance de DisplayInfo
            log: Afficher les résultats
        """


        monitors_info = display_info.get_all_monitors_info()
        max_index = len(monitors_info) - 1

        # Valider chaque config
        for monitor_index, image_path in monitor_configs:
            if monitor_index < 0 or monitor_index > max_index:
                if log:
                    print(f"Error: Monitor index {monitor_index} doesn't exist (max: {max_index})")
                return False

            path = Path(image_path)
            if not path.exists():
                if log:
                    print(f"Error: Image not found at {image_path}")
                return False

        try:
            CLSID_DesktopWallpaper = GUID(
                "{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}"
            )

            # Créer l'instance
            desktop_wallpaper = CoCreateInstance(CLSID_DesktopWallpaper, interface=IDesktopWallpaper)

            # Changer pour chaque moniteur
            for monitor_index, image_path in monitor_configs:
                abs_path = str(Path(image_path).absolute())

                # Récupérer l'ID du moniteur (comtypes retourne automatiquement)
                monitor_id = desktop_wallpaper.GetMonitorDevicePathAt(monitor_index)

                # Définir le wallpaper
                desktop_wallpaper.SetWallpaper(monitor_id, abs_path)


            if log:
                print("Wallpapers changed successfully!")
            return True

        except Exception as e:
            if log:
                print(f"Error: {e}")
            return False

    """@staticmethod
    def _read_desktop_registry(log=False):
        ""Lit la config actuelle du registre""
        try:
            # Ouvrir la clé du registre
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Desktop",
                0,
                winreg.KEY_READ
            )

            # Lire les valeurs importantes
            wallpaper, _ = winreg.QueryValueEx(key, "Wallpaper")
            style, _ = winreg.QueryValueEx(key, "WallpaperStyle")
            tile, _ = winreg.QueryValueEx(key, "TileWallpaper")

            if log:
                print(f"Wallpaper actuel: {wallpaper}")
                print(f"Style: {style}")
                print(f"Tile: {tile}")

            # Fermer la clé
            winreg.CloseKey(key)

            return {"wallpaper": wallpaper, "style": style, "tile": tile}


        except Exception as e:
            print(f"Error reading registry: {e}")
            return None"""
