import asyncio
from typing import Optional, Dict
from session import CallContext
from src.server.models import Actor
from src.utils.ari_proxy_client import AriProxyClient
from datetime import datetime, timezone
import queue
from src.server.network.base import PortAllocationStrategy, SequentialPortAllocationStrategy
from src.exceptions import NoPortAvailableException


class SessionManager:
    async def register(self, call_id: str):
        raise NotImplementedError

    async def get(self, call_id) -> Optional[CallContext]:
        raise NotImplementedError

    async def has_session(self, call_id) -> bool:
        raise NotImplementedError

    async def update_outbound(self, call_id, host: str, port: int) -> None:
        raise NotImplementedError

    def deactivate(self, call_id: str):
        raise NotImplementedError

    def activate(self, call_id: str):
        raise NotImplementedError

    async def terminate(self, call_id, actor: Actor) -> None:
        raise NotImplementedError


class InMemorySessionManager(SessionManager):
    def __init__(self, host: str,
                 ari_base_url: str,
                 port_allocation_strategy: PortAllocationStrategy):
        self.host = host
        self.call_contexts: Dict[str, CallContext] = {}
        self.assignable_ports: queue.Queue = queue.Queue()
        self.ari_proxy_client = AriProxyClient(ari_base_url)

        for port in port_allocation_strategy.allocate():
            self.assignable_ports.put(port)

    async def register(self, call_id):
        port = await self.get_available_port()
        self.call_contexts[call_id] = CallContext(
            callId=call_id,
            inbound={"host": self.host, "port": port},
            outbound={}
        )

    async def get(self, call_id) -> Optional[CallContext]:
        try:
            return self.call_contexts[call_id]
        except KeyError:
            pass
        return None

    async def has_session(self, call_id) -> bool:
        return call_id in self.call_contexts

    async def update_outbound(self, call_id, host: str, port: int) -> None:
        self.call_contexts[call_id].outbound = {"host": host, "port": port}

    async def deactivate(self, call_id: str):
        self.call_contexts[call_id].status = CallContext.Status.INACTIVE

    async def activate(self, call_id: str):
        self.call_contexts[call_id].status = CallContext.Status.ACTIVE

    async def terminate(self, call_id, actor: Actor) -> None:
        await self.deactivate(call_id)
        await asyncio.sleep(1)
        if actor == Actor.DE:
            try:
                self.ari_proxy_client.post_end_call(call_id,
                                                    datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                                                    )
            except Exception as e:
                pass
        self.assignable_ports.put(self.call_contexts[call_id].inbound.get("port"))
        del self.call_contexts[call_id]

    async def get_available_port(self) -> int:
        if self.assignable_ports.empty():
            raise NoPortAvailableException("No available ports for allocation")
        return self.assignable_ports.get()

    async def get_available_port(self) -> int:
        if self.assignable_ports.empty():
            raise NoPortAvailableException("No available ports for allocation")
        return self.assignable_ports.get()
