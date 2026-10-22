from typing import Protocol


class DataSource(Protocol):
    name: str

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def ping(self) -> bool: ...


class NullSource:
    def __init__(self, name: str) -> None:
        self.name = name

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def ping(self) -> bool:
        return True
