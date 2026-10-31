class GetLockTimeout(Exception):
    def __init__(self, name: str, timeout: int):
        super().__init__(f"get LOCK:{name} timeout({timeout})")


class AuthFailed(Exception):
    def __init__(self, msg: str):
        super().__init__(f"auth failed: {msg}")


class ResourceNotFound(Exception):
    def __init__(self, resource: str) -> None:
        super().__init__("Resource not found: {}")


class PermissionDeny(Exception):
    def __init__(self, detail: str = "Permission deny") -> None:
        super().__init__(detail)
