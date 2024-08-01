from typing import TypeVar, Generic, List
import logging
from abc import ABC
logger = logging.getLogger(__name__)

WorkerInputType = TypeVar("WorkerInputType")


class PortAllocationStrategy(ABC):
    def allocate(self) -> List[int]:
        raise NotImplementedError


class SequentialPortAllocationStrategy(PortAllocationStrategy):
    def allocate(self) -> List[int]:
        return list(range(9000, 9999))
