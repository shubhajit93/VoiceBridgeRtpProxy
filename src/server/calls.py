import logging
from src.session.session_manager import CallContext, SessionManager
from typing import Optional
from dotenv import load_dotenv
import os
from utils.voice_bridge_client import VoiceBridgeClient
from utils.ari_proxy_client import AriProxyClient

load_dotenv()

RTP_PROXY_UPSTREAM_WS_URL = os.getenv("RTP_PROXY_UPSTREAM_WS_URL", "ws://127.0.0.1:3001/connect_call")
RTP_PROXY_HOST_ADDRESS = os.getenv("RTP_PROXY_HOST_ADDRESS", "localhost")
ARI_PROXY_API_BASE_URL = os.getenv("ARI_PROXY_API_BASE_URL", "localhost")


class StreamHandler:
    def __init__(self,
                 call_id: str,
                 session_manager: SessionManager,
                 logger: Optional[logging.Logger] = None):
        self.call_id = call_id
        self.session_manager: SessionManager = session_manager
        self.logger = logger or logging.getLogger(__name__)

    async def initiate(self):
        from src.server.worker.stream_opt_out_worker import StreamOptOutWorker
        from src.server.worker.stream_opt_in_worker import StreamOptInWorker
        from src.utils.voice_bridge_client import VoiceBridgeClient
        call_context = await self.session_manager.get(self.call_id)
        ws_client = None
        opt_in_worker = None
        opt_out_worker = None
        try:
            ws_client = VoiceBridgeClient(f"{RTP_PROXY_UPSTREAM_WS_URL}/{call_context.callId}", on_message_callback=None)
            ari_client = AriProxyClient(ARI_PROXY_API_BASE_URL)
            opt_in_worker = StreamOptInWorker(call_context, ws_client)
            opt_out_worker = StreamOptOutWorker(call_context, self.session_manager, ws_client)
            await self.session_manager.activate(self.call_id)
            opt_in_worker.start()
            opt_out_worker.start()
            self.logger.info(f"Streaming Workers for call id {call_context.callId} started successfully.")
        except Exception as e:
            self.logger.error(
                f"Exception occurred during initiating workers for call id {call_context.callId}: {e}",
                exc_info=True)
            self._clean_up(opt_in_worker, opt_out_worker, ws_client)

    def _clean_up(self, opt_in_worker, opt_out_worker, ws_client):
        try:
            opt_in_worker.terminate()
        except Exception as e:
            pass
        if opt_out_worker:
            try:
                opt_out_worker.terminate()
            except Exception as e:
                pass
        if ws_client:
            try:
                ws_client.close()
            except Exception as e:
                pass
