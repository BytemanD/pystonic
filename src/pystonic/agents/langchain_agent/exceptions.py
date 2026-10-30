class ModelsIsEmpty(Exception):
    def __init__(self):
        super().__init__("models is empty")


class AllModelsFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("all models failed, errors: {}", errors)


class PermissionDeny(Exception):
    def __init__(self, detail: str):
        super().__init__("permission deny: {}", detail)


class SessionNotFount(Exception):
    def __init__(self, session_id: str):
        super().__init__("session not found: {}", session_id)
