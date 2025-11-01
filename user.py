

class User:
    is_logged_in = False
    user_id = None
    vorname = ''
    nachname = ''
    email = ''
    profile = ''

    def __init__(self, user):
        self.is_logged_in = True
        self.user_id = user['user_id']
        self.vorname = user['vorname']
        self.nachname = user['nachname']
        self.email = user['email']
        self.profil = user['profil']
