class CreateDockerClientFailed(Exception):
    def __init__(self, reason) -> None:
        super().__init__(f"create docker client failed: {reason}")


class ContainerNotExists(Exception):
    def __init__(self, id_or_name) -> None:
        super().__init__(f"container {id_or_name} not exists")


class ContainerNotRunning(Exception):
    def __init__(self, id_or_name) -> None:
        super().__init__(f"container {id_or_name} is not running")


class ContainerStatusNotMatch(Exception):
    def __init__(self, id_or_name: str, actual: str, expect: list[str]) -> None:
        super().__init__(f"container {id_or_name} status is {actual}, expect {expect}")
