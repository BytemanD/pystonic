from pystonic.common.exceptions import ResourceNotFound


class ModelsIsEmpty(Exception):
    def __init__(self):
        super().__init__("models is empty")


class AllModelsFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__(f"all models failed, errors: {errors}")


class PermissionDeny(Exception):
    def __init__(self, detail: str):
        super().__init__(f"permission deny: {detail}")


class SessionNotFound(ResourceNotFound):
    def __init__(self, session_id: str):
        super().__init__(f"Session({session_id})")
