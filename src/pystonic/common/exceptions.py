class GetDBLockTimeout(Exception):
    def __init__(self, name: str):
        super().__init__(f"get LOCK:{name} timeout")


class AuthFailed(Exception):
    def __init__(self, msg: str):
        super().__init__(f"auth failed: {msg}")
