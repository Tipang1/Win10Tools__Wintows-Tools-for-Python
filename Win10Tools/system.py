try:
    # Imports standard Python
    import os
    import subprocess
    import threading
    import time
    from datetime import datetime, timedelta

    # Imports système Windows (ctypes, comtypes)
    import ctypes
    from ctypes import cast, POINTER, c_float, c_int, c_void_p
    from comtypes import CoCreateInstance, IUnknown, COMMETHOD, GUID, HRESULT

    # Imports bibliothèques tierces
    import psutil
    import pyperclip
    import tkinter as tk
    from tkinter import font
    from win10toast import ToastNotifier

except ModuleNotFoundError as e:
    print(e)

# GUIDs pour l'API Audio Windows
CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_IMMDeviceEnumerator = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
IID_IAudioEndpointVolume = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")

# Constantes
CLSCTX_ALL = 23
EDataFlow_eRender = 0  # Sortie audio (haut-parleurs)
ERole_eMultimedia = 1  # Rôle multimédia


# Interface pour le dispositif multimédia
class IMMDevice(IUnknown):
    _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
    _methods_ = [
        COMMETHOD([], HRESULT, "Activate",
                  (['in'], POINTER(GUID), "iid"),
                  (['in'], c_int, "dwClsCtx"),
                  (['in'], c_void_p, "pActivationParams"),
                  (['out', 'retval'], POINTER(POINTER(IUnknown)), "ppInterface"))
    ]

# Interface pour énumérer les dispositifs audio
class IMMDeviceEnumerator(IUnknown):
    _iid_ = IID_IMMDeviceEnumerator
    _methods_ = [
        COMMETHOD([], HRESULT, "EnumAudioEndpoints"),
        COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint",
                  (['in'], c_int, "dataFlow"),
                  (['in'], c_int, "role"),
                  (['out', 'retval'], POINTER(POINTER(IMMDevice)), "ppDevice"))  # <-- Changé ici
    ]

# Interface pour contrôler le volume
class IAudioEndpointVolume(IUnknown):
    _iid_ = IID_IAudioEndpointVolume
    _methods_ = [
        COMMETHOD([], HRESULT, "RegisterControlChangeNotify",
                  (['in'], POINTER(IUnknown), "pNotify")),
        COMMETHOD([], HRESULT, "UnregisterControlChangeNotify",
                  (['in'], POINTER(IUnknown), "pNotify")),
        COMMETHOD([], HRESULT, "GetChannelCount",
                  (['out'], POINTER(ctypes.c_uint), "pnChannelCount")),
        COMMETHOD([], HRESULT, "SetMasterVolumeLevel",
                  (['in'], c_float, "fLevelDB"),
                  (['in'], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "SetMasterVolumeLevelScalar",
                  (['in'], c_float, "fLevel"),
                  (['in'], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetMasterVolumeLevel",
                  (['out'], POINTER(c_float), "pfLevelDB")),
        COMMETHOD([], HRESULT, "GetMasterVolumeLevelScalar",
                  (['out'], POINTER(c_float), "pfLevel")),
        COMMETHOD([], HRESULT, "SetChannelVolumeLevel",
                  (['in'], ctypes.c_uint, "nChannel"),
                  (['in'], c_float, "fLevelDB"),
                  (['in'], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "SetChannelVolumeLevelScalar",
                  (['in'], ctypes.c_uint, "nChannel"),
                  (['in'], c_float, "fLevel"),
                  (['in'], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetChannelVolumeLevel",
                  (['in'], ctypes.c_uint, "nChannel"),
                  (['out'], POINTER(c_float), "pfLevelDB")),
        COMMETHOD([], HRESULT, "GetChannelVolumeLevelScalar",
                  (['in'], ctypes.c_uint, "nChannel"),
                  (['out'], POINTER(c_float), "pfLevel")),
        COMMETHOD([], HRESULT, "SetMute",
                  (['in'], ctypes.c_int, "bMute"),
                  (['in'], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetMute",
                  (['out'], POINTER(ctypes.c_int), "pbMute")),
    ]


class SystemManager:
    """Gestion des paramètres système Windows"""

    class Volume:
        @staticmethod
        def get_volume(log=False):
            """Récupère le volume système actuel (0-100)"""
            try:
                # Créer l'énumérateur de dispositifs audio
                device_enumerator = CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    CLSCTX_ALL
                )

                # Récupérer le dispositif audio par défaut
                audio_device = device_enumerator.GetDefaultAudioEndpoint(EDataFlow_eRender, ERole_eMultimedia)

                # Obtenir l'interface de contrôle du volume
                volume_interface = audio_device.Activate(IID_IAudioEndpointVolume, CLSCTX_ALL, None)
                volume_interface = cast(volume_interface, POINTER(IAudioEndpointVolume))

                # Récupérer le volume (valeur entre 0.0 et 1.0)
                current_volume = volume_interface.GetMasterVolumeLevelScalar()
                volume_percent = round(current_volume * 100)

                if log:
                    print(f"Current volume: {volume_percent}%")

                return volume_percent

            except Exception as e:
                if log:
                    print(f"Error getting volume: {e}")
                return None

        @staticmethod
        def set_volume(volume, log=False):
            """Définit le volume système (0-100)"""
            if not 0 <= volume <= 100:
                if log:
                    print(f"Error: Volume must be between 0 and 100 (got {volume})")
                return False

            try:
                # Créer l'énumérateur de dispositifs audio
                device_enumerator = CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    CLSCTX_ALL
                )

                # Récupérer le dispositif audio par défaut
                audio_device = device_enumerator.GetDefaultAudioEndpoint(EDataFlow_eRender, ERole_eMultimedia)

                # Obtenir l'interface de contrôle du volume
                volume_interface = audio_device.Activate(IID_IAudioEndpointVolume, CLSCTX_ALL, None)
                volume_interface = cast(volume_interface, POINTER(IAudioEndpointVolume))

                # Convertir le volume de 0-100 en 0.0-1.0
                volume_scalar = volume / 100.0

                # Définir le volume
                volume_interface.SetMasterVolumeLevelScalar(volume_scalar, None)

                if log:
                    print(f"Volume set to {volume}%")

                return True

            except Exception as e:
                if log:
                    print(f"Error setting volume: {e}")
                return False

        @staticmethod
        def mute(log=False):
            """Active/désactive le mute (toggle)"""
            try:
                # Créer l'énumérateur de dispositifs audio
                device_enumerator = CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    CLSCTX_ALL
                )

                # Récupérer le dispositif audio par défaut
                audio_device = device_enumerator.GetDefaultAudioEndpoint(EDataFlow_eRender, ERole_eMultimedia)

                # Obtenir l'interface de contrôle du volume
                volume_interface = audio_device.Activate(IID_IAudioEndpointVolume, CLSCTX_ALL, None)
                volume_interface = cast(volume_interface, POINTER(IAudioEndpointVolume))

                # Récupérer l'état actuel du mute
                is_muted = volume_interface.GetMute()

                # Inverser l'état (toggle)
                new_mute_state = 0 if is_muted else 1
                volume_interface.SetMute(new_mute_state, None)

                if log:
                    if is_muted:
                        print("Audio unmuted")
                    else:
                        print("Audio muted")

                return not is_muted  # Retourne le nouvel état

            except Exception as e:
                if log:
                    print(f"Error toggling mute: {e}")
                return None

    class Power:
        @staticmethod
        def lock_computer(log=False):
            """Verrouille l'ordinateur"""
            try:
                ctypes.windll.user32.LockWorkStation()
                if log:
                    print("Computer locked!")
                return True
            except Exception as e:
                if log:
                    print(f"Error locking computer: {e}")
                return False

        @staticmethod
        def shutdown(log=False):
            """Éteint l'ordinateur"""
            try:
                if log:
                    print("Shutting down...")
                os.system("shutdown /s /t 0")
                return True
            except Exception as e:
                if log:
                    print(f"Error shutting down: {e}")
                return False

        @staticmethod
        def reboot(log=False):
            """Redémarre l'ordinateur"""
            try:
                if log:
                    print("Restarting...")
                os.system("shutdown /r /t 0")
                return True
            except Exception as e:
                if log:
                    print(f"Error restarting: {e}")
                return False

        @staticmethod
        def sleep(log=False):
            """Met l'ordinateur en veille"""
            try:
                if log:
                    print("Going to sleep...")
                ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                return True
            except Exception as e:
                if log:
                    print(f"Error going to sleep: {e}")
                return False

    class Apps:
        """Gestion des applications Windows"""

        @staticmethod
        def open(app_path, log=False, _internal=False):
            """Ouvre une application par son chemin ou commande"""
            import subprocess

            if _internal:
                # Appelé depuis une autre méthode Apps, on lève l'exception
                subprocess.Popen([app_path])
                return True
            else:
                # Appelé directement, on gère l'erreur
                try:
                    subprocess.Popen([app_path])
                    if log:
                        print(f"Application opened: {app_path}")
                    return True
                except Exception as e:
                    if log:
                        print(f"Error opening application: {e}")
                    return False

        @staticmethod
        def notepad(file_path=None, log=False):
            """Ouvre Notepad (optionnellement avec un fichier)"""
            try:
                if file_path:
                    subprocess.Popen(['notepad.exe', file_path])
                else:
                    subprocess.Popen(['notepad.exe'])

                if log:
                    print(f"Notepad opened{' with file' if file_path else ''}")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Notepad: {e}")
                return False

        @staticmethod
        def calculator(log=False):
            """Ouvre la calculatrice Windows"""
            try:
                subprocess.Popen(['calc.exe'])
                if log:
                    print("Calculator opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Calculator: {e}")
                return False

        @staticmethod
        def explorer(path=None, log=False):
            """Ouvre l'Explorateur Windows (optionnellement à un chemin spécifique)"""
            try:
                if path:
                    SystemManager.Apps.open(f'explorer.exe "{path}"', _internal=True)
                else:
                    SystemManager.Apps.open('explorer.exe', _internal=True)

                if log:
                    print(f"Explorer opened{f' at {path}' if path else ''}")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Explorer: {e}")
                return False

        @staticmethod
        def paint(log=False):
            """Ouvre Paint"""
            try:
                SystemManager.Apps.open('mspaint.exe', _internal=True)
                if log:
                    print("Paint opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Paint: {e}")
                return False

        @staticmethod
        def cmd(log=False):
            """Ouvre l'invite de commande"""
            try:
                SystemManager.Apps.open('cmd.exe', _internal=True)
                if log:
                    print("Command Prompt opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening CMD: {e}")
                return False

        @staticmethod
        def powershell(log=False):
            """Ouvre PowerShell"""
            try:
                SystemManager.Apps.open('powershell.exe', _internal=True)
                if log:
                    print("PowerShell opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening PowerShell: {e}")
                return False

        @staticmethod
        def task_manager(log=False):
            """Ouvre le Gestionnaire des tâches"""
            try:
                SystemManager.Apps.open('taskmgr.exe', _internal=True)
                if log:
                    print("Task Manager opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Task Manager: {e}")
                return False

        @staticmethod
        def control_panel(log=False):
            """Ouvre le Panneau de configuration"""
            try:
                SystemManager.Apps.open('control.exe', _internal=True)
                if log:
                    print("Control Panel opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Control Panel: {e}")
                return False

        @staticmethod
        def settings(log=False):
            """Ouvre les Paramètres Windows 10"""
            try:
                SystemManager.Apps.open('ms-settings:', _internal=True)
                if log:
                    print("Windows Settings opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Settings: {e}")
                return False

        @staticmethod
        def snipping_tool(log=False):
            """Ouvre l'Outil Capture d'écran"""
            try:
                SystemManager.Apps.open('snippingtool.exe', _internal=True)
                if log:
                    print("Snipping Tool opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Snipping Tool: {e}")
                return False

        @staticmethod
        def wordpad(log=False):
            """Ouvre WordPad"""
            try:
                SystemManager.Apps.open('wordpad.exe', _internal=True)
                if log:
                    print("WordPad opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening WordPad: {e}")
                return False

        @staticmethod
        def character_map(log=False):
            """Ouvre la Table des caractères"""
            try:
                SystemManager.Apps.open('charmap.exe', _internal=True)
                if log:
                    print("Character Map opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Character Map: {e}")
                return False

        @staticmethod
        def registry_editor(log=False):
            """Ouvre l'Éditeur du Registre (nécessite les droits admin)"""
            try:
                SystemManager.Apps.open('regedit.exe', _internal=True)
                if log:
                    print("Registry Editor opened")
                return True
            except Exception as e:
                if log:
                    print(f"Error opening Registry Editor: {e}")
                return False

    class Info:
        """Informations système"""

        @staticmethod
        def ram(log=False):
            """Récupère les infos de la RAM (utilisée/totale en GB)"""
            try:
                mem = psutil.virtual_memory()
                total_gb = mem.total / (1024 ** 3)
                used_gb = mem.used / (1024 ** 3)
                available_gb = mem.available / (1024 ** 3)
                percent = mem.percent

                if log:
                    print(f"RAM: {used_gb:.2f}GB / {total_gb:.2f}GB ({percent}% used)")
                    print(f"Available: {available_gb:.2f}GB")

                return {
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'available_gb': round(available_gb, 2),
                    'percent': percent
                }
            except Exception as e:
                if log:
                    print(f"Error getting RAM info: {e}")
                return None

        @staticmethod
        def cpu(log=False):
            """Récupère l'utilisation du CPU"""
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count(logical=True)
                cpu_freq = psutil.cpu_freq()

                if log:
                    print(f"CPU Usage: {cpu_percent}%")
                    print(f"CPU Cores: {cpu_count}")
                    print(f"CPU Frequency: {cpu_freq.current:.2f} MHz")

                return {
                    'percent': cpu_percent,
                    'cores': cpu_count,
                    'frequency_mhz': round(cpu_freq.current, 2)
                }
            except Exception as e:
                if log:
                    print(f"Error getting CPU info: {e}")
                return None

        @staticmethod
        def disk(disk_info='C:', log=False):
            """Récupère les infos du disque C:"""
            import psutil
            try:
                disk = psutil.disk_usage(disk_info)
                total_gb = disk.total / (1024 ** 3)
                used_gb = disk.used / (1024 ** 3)
                free_gb = disk.free / (1024 ** 3)
                percent = disk.percent

                if log:
                    print(f"Disk {disk_info} {used_gb:.2f}GB / {total_gb:.2f}GB ({percent}% used)")
                    print(f"Free: {free_gb:.2f}GB")

                return {
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'percent': percent
                }
            except Exception as e:
                if log:
                    print(f"Error getting disk info: {e}")
                return None

        @staticmethod
        def uptime(log=False):
            """Récupère le temps depuis le démarrage"""
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = datetime.now().timestamp() - boot_time
                uptime_delta = timedelta(seconds=uptime_seconds)

                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                if log:
                    print(f"Uptime: {days}d {hours}h {minutes}m {seconds}s")

                return {
                    'days': days,
                    'hours': hours,
                    'minutes': minutes,
                    'seconds': seconds,
                    'total_seconds': int(uptime_seconds)
                }
            except Exception as e:
                if log:
                    print(f"Error getting uptime: {e}")
                return None

    class Notifications:
        """Gestion des notifications Windows"""

        class Send:
            """Envoi de notifications"""

            @staticmethod
            def windows(title, message, duration: float = None, duration_preset: str = None, icon=None, log=False):
                """Envoie une notification Windows native

                Args:
                    title: Titre de la notification
                    message: Message de la notification
                    duration: Nombre indiquant la durée d'apparition de la notification en secondes
                    duration_preset: "short" ou "long" (3s ou 7s), remplace la durée définie avec le paramètre 'duration'
                    icon: Chemin vers une icône .ico (optionnel)
                    log: Afficher un message de confirmation
                """
                try:
                    # Créer la notification
                    toast = ToastNotifier()

                    if duration is None and duration_preset is None:
                        duration_preset = "short"

                    if duration_preset in ["short", "long"]:
                        if duration_preset == "long":
                            duration = 7
                        else:
                            duration = 3

                    """
                    # Ajouter une icône si fournie
                    if icon:
                        toast.set_audio(audio.Default, loop=False)
                    """

                    while threading.activeCount() > 1:
                        pass

                    # Afficher la notification
                    toast.show_toast(title, message, duration=duration, threaded=True)

                    if log:
                        print(f"Notification sent: {title}")

                    return True

                except Exception as e:
                    if log:
                        print(f"Error sending notification: {e}")
                    return False

            @staticmethod
            def custom(title, message, style="default", duration=3, log=False):
                """Envoie une notification personnalisée (style Steam)"""
                try:

                    # Créer la fenêtre
                    root = tk.Tk()
                    root.overrideredirect(True)  # Pas de bordures
                    root.attributes('-topmost', True)  # Toujours au premier plan

                    # Styles selon le paramètre
                    styles = {
                        "default": {"bg": "#2a2a2a", "fg": "white"},
                        "steam": {"bg": "#171a21", "fg": "#c7d5e0"},
                        "success": {"bg": "#28a745", "fg": "white"},
                        "error": {"bg": "#dc3545", "fg": "white"},
                        "warning": {"bg": "#ffc107", "fg": "black"}
                    }

                    colors = styles.get(style, styles["default"])

                    # Configurer la fenêtre
                    root.configure(bg=colors["bg"])

                    # Frame principale
                    frame = tk.Frame(root, bg=colors["bg"], padx=15, pady=10)
                    frame.pack()

                    # Titre
                    title_font = font.Font(family="Segoe UI", size=12, weight="bold")
                    title_label = tk.Label(frame, text=title, font=title_font,
                                           bg=colors["bg"], fg=colors["fg"])
                    title_label.pack(anchor="w")

                    # Message
                    msg_font = font.Font(family="Segoe UI", size=10)
                    msg_label = tk.Label(frame, text=message, font=msg_font,
                                         bg=colors["bg"], fg=colors["fg"], wraplength=250)
                    msg_label.pack(anchor="w", pady=(5, 0))

                    # Positionner en bas à droite
                    root.update_idletasks()
                    width = root.winfo_width()
                    height = root.winfo_height()
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    x = screen_width - width - 20
                    y = screen_height - height - 60
                    root.geometry(f"+{x}+{y}")

                    if log:
                        print(f"Custom notification sent: {title}")

                    # Afficher la fenêtre
                    root.deiconify()
                    root.update()

                    # Fermer après duration secondes (en millisecondes)
                    def close_notification():
                        try:
                            root.destroy()
                        except:
                            pass

                    root.after(int(duration * 1000), close_notification)

                    # Garder la fenêtre active pendant la durée
                    for _ in range(int(duration * 10)):
                        try:
                            root.update()
                            time.sleep(0.1)
                        except:
                            break

                    return True

                except Exception as e:
                    if log:
                        print(f"Error sending custom notification: {e}")
                    return False

    class Clipboard:
        """Gestion du presse-papiers Windows"""

        @staticmethod
        def copy(text, log=False):
            """Copie du texte dans le presse-papiers"""
            try:
                pyperclip.copy(text)

                if log:
                    print(f"Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}")

                return True
            except Exception as e:
                if log:
                    print(f"Error copying to clipboard: {e}")
                return False

        @staticmethod
        def paste(log=False):
            """Récupère le texte du presse-papiers"""
            try:
                text = pyperclip.paste()

                if log:
                    print(f"Clipboard content: {text[:50]}{'...' if len(text) > 50 else ''}")

                return text
            except Exception as e:
                if log:
                    print(f"Error reading clipboard: {e}")
                return None

        @staticmethod
        def clear(log=False):
            """Vide le presse-papiers"""
            try:
                pyperclip.copy('')

                if log:
                    print("Clipboard cleared")

                return True
            except Exception as e:
                if log:
                    print(f"Error clearing clipboard: {e}")
                return False

    class Process:
        """Gestion des processus Windows"""

        @staticmethod
        def list_all(log=False):
            """Liste tous les processus"""
            try:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        info = proc.info
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu': info['cpu_percent'],
                            'memory_mb': info['memory_info'].rss / (1024 ** 2) if info['memory_info'] else 0
                        })
                    except:
                        pass

                if log:
                    for p in processes[:10]:  # Afficher les 10 premiers
                        print(f"PID {p['pid']}: {p['name']} - CPU: {p['cpu']}% - RAM: {p['memory_mb']:.1f}MB")

                return processes
            except Exception as e:
                if log:
                    print(f"Error: {e}")
                return None

        @staticmethod
        def kill(pid_or_name, log=False):
            """Tue un processus par PID ou nom"""
            try:
                if isinstance(pid_or_name, int):
                    proc = psutil.Process(pid_or_name)
                    proc.terminate()
                    name = proc.name()
                else:
                    killed = False
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'].lower() == pid_or_name.lower():
                            proc.terminate()
                            killed = True
                            break
                    if not killed:
                        if log:
                            print(f"Process not found: {pid_or_name}")
                        return False
                    name = pid_or_name

                if log:
                    print(f"Process killed: {name}")
                return True
            except Exception as e:
                if log:
                    print(f"Error: {e}")
                return False

        @staticmethod
        def exists(name, log=False):
            """Vérifie si un processus existe"""
            try:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == name.lower():
                        if log:
                            print(f"Process found: {name}")
                        return True
                if log:
                    print(f"Process not found: {name}")
                return False
            except Exception as e:
                if log:
                    print(f"Error: {e}")
                return None


