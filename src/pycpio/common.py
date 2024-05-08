from logging import Logger, getLogger
from typing import Protocol, TypedDict


class Loggified(Protocol):
    logger: Logger


class LoggedKwargs(TypedDict, total=False):
    logger: Logger


class Logged(Loggified):
    __slots__ = ("logger",)

    def __init__(self, logger: Logger = None, **kwargs) -> None:
        self.logger = logger or getLogger(self.__class__.__qualname__)
