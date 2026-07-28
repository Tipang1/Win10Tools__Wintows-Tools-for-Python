from .system import SystemManager

class UselessClass:
    @staticmethod
    def do_nothing(print_result=False):
        """Ne fait littéralement rien"""
        if print_result:
            print("Successfully did nothing!")
        pass

    @staticmethod
    def get_current_time_and_ignore_it(print_result=False):
        """Récupère l'heure actuelle puis l'ignore complètement. Une véritable perte de temps !"""
        import time
        current_time = time.time()
        if print_result:
            print("Got the time... and promptly forgot it!")
        # On ne retourne rien, total waste

    @staticmethod
    def count_to_zero(print_result=False):
        """Compte jusqu'à zéro (spoiler: c'est rapide)"""
        if print_result:
            print("Counting to zero: Done!")
        return 0

    @staticmethod
    def is_computer_on(print_result=False):
        """Vérifie si l'ordinateur est allumé (si ce code s'exécute, c'est oui)"""
        if print_result:
            print("Checking if computer is on... YES! (obviously)")
        return True

    @staticmethod
    def set_volume_to_current_one(print_result=False):
        """Change le volume... vers le volume actuel (totalement inutile)"""
        current = SystemManager.get_volume()
        SystemManager.set_volume(current)
        if print_result:
            print(f"Volume successfully changed from {current}% to... {current}%! 🎉")
        return current

    @staticmethod
    def return_false(print_result=False):
        """Retourne False. C'est tout. Vraiment."""
        if print_result:
            print("Returning False... for no reason at all!")
        return False

    @staticmethod
    def return_true(print_result=False):
        """Retourne True. Parce que pourquoi pas."""
        if print_result:
            print("Returning True... because True is good, right?")
        return True

    @staticmethod
    def return_none(print_result=False):
        """Retourne None. Le vide absolu."""
        if print_result:
            print("Returning None... the void stares back.")
        return None

    @staticmethod
    def infinite_looooooooooop(print_result=False):
        """ You wanna get stuck in an infinite loop but can't figure out how? Just execute this! """
        if print_result:
            print("You're stuck now!")
        return UselessClass.infinite_looooooooooop(print_result)
