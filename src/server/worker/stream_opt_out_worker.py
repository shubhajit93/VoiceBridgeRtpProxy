import audioop
import time
import asyncio
from src.server.worker.base import ThreadAsyncWorker
from src.server.models import Actor
from typing import Optional
import logging
import gi
from src.session import CallContext
from src.session.session_manager import SessionManager
from server.models.asterisk_models import PacketGenerator, Packet
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

# Initialize GStreamer
Gst.init(None)


class StreamOptOutWorker(ThreadAsyncWorker):
    def __init__(self,
                 call_context: CallContext,
                 session_manager: SessionManager,
                 ws_client,
                 logger: Optional[logging.Logger] = None):
        super().__init__()
        self.call_context = call_context
        self.session_manager = session_manager
        self.ws_client = ws_client
        self.pipeline = None
        self.logger = logger or logging.getLogger(__name__)

    def start_pipeline(self):
        self.pipeline = Gst.Pipeline.new("udp_pipeline")

        data_injector = self._prepare_outboud_injector()
        outbound_udp = self._prepare_out_bound(self.call_context.outbound['host'],
                                                   self.call_context.outbound['port'])
        rtp_payload_generator = Gst.ElementFactory.make("rtppcmupay", "rtppay")
        self._add_pipeline_elements(data_injector, outbound_udp, rtp_payload_generator)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.ws_client.on_message_callback = lambda message: self.on_websocket_message(data_injector, message)

    def _add_pipeline_elements(self, data_injector, outbound_udp, rtp_payload_generator):
        self.pipeline.add(data_injector)
        self.pipeline.add(rtp_payload_generator)
        self.pipeline.add(outbound_udp)
        # Link the elements
        data_injector.link(rtp_payload_generator)
        rtp_payload_generator.link(outbound_udp)

    def _prepare_out_bound(self, host: str, port: int):
        udpsink = Gst.ElementFactory.make("udpsink", "udpsink")
        udpsink.set_property("host", host)
        udpsink.set_property("port", port)
        udpsink.set_property("sync", False)
        udpsink.set_property("async", False)
        return udpsink

    def _prepare_outboud_injector(self):
        appsrc = Gst.ElementFactory.make("appsrc", "appsrc")
        appsrc.set_property("is-live", True)
        appsrc.set_property("block", True)
        appsrc.set_property("format", 3)
        appsrc.set_property("do-timestamp", True)
        appsrc.set_property("caps", Gst.caps_from_string("audio/x-mulaw, rate=(int)8000, channels=(int)1"))
        return appsrc

    def on_websocket_message(self, appsrc, message):
        packet: Packet = Packet(message)

        if packet.has_terminate:
            self.session_manager.deactivate(self.call_context.callId)
        elif packet.has_payload:
            audio_data = packet.payload
            for i in range(0, len(audio_data), 320):
                chunk = audio_data[i:i + 320]

                chunk = audioop.lin2ulaw(chunk, 2)
                buf = Gst.Buffer.new_allocate(None, len(chunk), None)
                buf.fill(0, chunk)
                appsrc.emit('push-buffer', buf)
                time.sleep(0.020)

    def _run_loop(self):
        self.start_pipeline()
        while self.call_context.is_activate():
            time.sleep(1)
        self.pipeline.set_state(Gst.State.NULL)
        self.terminate()

    def terminate(self):
        try:
            self.logger.info(f"Terminating {self.__class__.__name__} of {self.call_context.callId}")
            self.ws_client.close()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.session_manager.terminate(self.call_context.callId, Actor.DE))
            finally:
                loop.close()
        except Exception as e:
            pass

