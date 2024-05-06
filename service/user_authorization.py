import hashlib


class User():
    def __init__(self, username, user_id=None):
        self.username = username
        self.user_id = user_id
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.user_id)

    @staticmethod
    def check_password(stored_password, provided_password):
        # Hash provided password and compare it with the stored hash
        hash_object = hashlib.sha256(provided_password.encode())
        hashed_password = hash_object.hexdigest()
        return hashed_password == stored_password
