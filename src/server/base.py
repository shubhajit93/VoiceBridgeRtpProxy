import logging
import os
import queue
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from src.server.models import OptCommonResponse, OptInResponse, OptOutRequest, OptCloseRequest, Actor
from src.server.network.base import PortAllocationStrategy, SequentialPortAllocationStrategy
from src.session.session_manager import SessionManager, InMemorySessionManager, CallContext
load_dotenv()

RTP_PROXY_UPSTREAM_WS_URL = os.getenv("RTP_PROXY_UPSTREAM_WS_URL", "ws://127.0.0.1:3001/connect_call")
RTP_PROXY_HOST_ADDRESS = os.getenv("RTP_PROXY_HOST_ADDRESS", "localhost")
ARI_PROXY_API_BASE_URL = os.getenv("ARI_PROXY_API_BASE_URL", "localhost")


class RtpProxyServer:
    def __init__(
            self,
            port_allocation_strategy: Optional[PortAllocationStrategy] = None,
            logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.router = APIRouter()
        self.router.add_api_route("/stream/optin/{call_id}", self.optin, methods=["GET"])
        self.router.add_api_route("/stream/optout", self.optout, methods=["POST"])
        self.router.add_api_route("/stream/optclose", self.optclose, methods=["POST"])
        self.available_ports: queue.Queue = queue.Queue()
        self.session_manager: SessionManager = InMemorySessionManager(RTP_PROXY_HOST_ADDRESS,
                                                                      ARI_PROXY_API_BASE_URL,
                                                                      port_allocation_strategy or SequentialPortAllocationStrategy())

    def get_router(self) -> APIRouter:
        return self.router

    async def optin(self, call_id: str) -> OptInResponse:
        if await self.session_manager.has_session(call_id):
            self.logger.warning(f"Call ID {call_id} already registered in call context")
            raise HTTPException(status_code=409, detail="already registered in call context")

        try:

            await self.session_manager.register(call_id)
            context: CallContext = await self.session_manager.get(call_id)
            self.logger.info(f"Session registered for call ID {call_id} : {context}")
            return OptInResponse(callId=call_id, host=RTP_PROXY_HOST_ADDRESS, port=context.inbound.get("port"))
        except ValidationError as ve:
            self.logger.warning("Port is not available to allocate", exc_info=ve)
            raise HTTPException(status_code=404, detail="Opt-in failed")
        except Exception as e:
            self.logger.error("Error in optin", exc_info=e)
            raise HTTPException(status_code=500, detail="Opt-in failed")

    async def optout(self, request: OptOutRequest) -> OptCommonResponse:
        from src.server.calls import StreamHandler

        call_id = request.callId

        if not await self.session_manager.has_session(call_id):
            self.logger.warning(f"Call ID {call_id} not found in call context")
            raise HTTPException(status_code=400, detail="Opt-out failed")

        call_context: CallContext = await self.session_manager.get(call_id)
        if call_context.is_active():
            self.logger.warning(f"Call ID {call_id} call is already in progress")
            raise HTTPException(status_code=409, detail="call is already in progress")

        await self.session_manager.update_outbound(call_id ,request.host, request.port)
        await StreamHandler(call_id, self.session_manager, self.logger).initiate()
        self.logger.info(f"Updated call context for call ID {call_id}")

        return OptCommonResponse(success=True, message="Opt-out successful")

    async def optclose(self, request: OptCloseRequest) -> OptCommonResponse:
        call_id = request.callId
        if not await self.session_manager.has_session(call_id):
            self.logger.warning(f"Call ID {call_id} not found in call context")
            raise HTTPException(status_code=400, detail="Opt-out failed")

        call_context: CallContext = await self.session_manager.get(call_id)

        if not call_context.is_active():
            self.logger.warning(f"Call ID {call_id} call is already in deactivated")
            raise HTTPException(status_code=409, detail="call is already in deactivated")

        await self.session_manager.terminate(call_id, Actor.ASTERISK)
        return OptCommonResponse(success=True, message="Opt-out successful")
