from aurora.security.models import User

class HiJackUser(User):
    is_hijacked: bool
