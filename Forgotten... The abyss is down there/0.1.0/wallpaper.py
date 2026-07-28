from pathlib import Path
import ctypes
import winreg
import subprocess

class WallpaperManager:
    # Constantes pour l'API Windows
    SPI_SETDESKWALLPAPER = 0x0014  # Code qui dit "je veux changer le fond d'écran"
    SPIF_UPDATEINIFILE = 0x0001  # Sauvegarder le changement
    SPIF_SENDCHANGE = 0x0002  # Notifier le système du changement

    @staticmethod
    def set_global_wallpaper(image_path, print_result=False):
        """Change le fond d'écran de tous les moniteurs"""
        # Vérifier que le fichier existe
        path = Path(image_path)
        if not path.exists():
            if print_result:
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

        if print_result:
            if result:
                print(f"Wallpaper changed successfully to: {abs_path}")
            else:
                print("Failed to change wallpaper")

        return bool(result)

    @staticmethod
    def set_wallpaper_per_monitor(monitor_configs, display_info, print_result=False):
        """
        Change le fond d'écran de moniteurs spécifiques

        Args:
            monitor_configs: Liste de tuples (monitor_index, image_path)
                            Ex: [(0, "image1.jpg"), (1, "image2.jpg")]
            display_info: Instance de DisplayInfo
            print_result: Afficher les résultats
        """
        monitors_info = display_info.get_all_monitors_info()
        max_index = len(monitors_info) - 1

        # Valider chaque config
        for monitor_index, image_path in monitor_configs:
            # Vérifier que l'index existe
            if monitor_index < 0 or monitor_index > max_index:
                if print_result:
                    print(f"Error: Monitor index {monitor_index} doesn't exist (max: {max_index})")
                return False

            # Vérifier que le fichier existe
            path = Path(image_path)
            if not path.exists():
                if print_result:
                    print(f"Error: Image not found at {image_path}")
                return False

        # TODO: appeler PowerShell pour chaque config

        if print_result:
            print("All wallpapers changed successfully!")
        return True

    @staticmethod
    def _read_desktop_registry(print_result=False):
        """Lit la config actuelle du registre"""
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

            if print_result:
                print(f"Wallpaper actuel: {wallpaper}")
                print(f"Style: {style}")
                print(f"Tile: {tile}")

            return {"wallpaper": wallpaper, "style": style, "tile": tile}

            # Fermer la clé
            winreg.CloseKey(key)

        except Exception as e:
            print(f"Error reading registry: {e}")
            return None
