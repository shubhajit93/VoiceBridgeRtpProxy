import gi
import time
import logging
from server.models.asterisk_models import PacketGenerator
from src.server.worker.base import ThreadAsyncWorker
from typing import Optional

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Initialize GStreamer
Gst.init(None)


class StreamOptInWorker(ThreadAsyncWorker):
    def __init__(self,
                 call_context,
                 ws_client,
                 logger: Optional[logging.Logger] = None):
        super().__init__()
        self.call_context = call_context
        self.ws_client = ws_client
        self.logger = logger or logging.getLogger(__name__)
        self.pipeline = None

    def start_pipeline(self):
        self.pipeline = self._prepare_inbound_pipeline()
        self._attach_udp_port(self.pipeline, self.call_context.inbound['port'])
        self._attach_data_handler(self.pipeline)
        self.pipeline.set_state(Gst.State.PLAYING)

    def _prepare_inbound_pipeline(self):
        return Gst.parse_launch(
            "rtpbin name=rtpbin "
            "udpsrc name=udpsrc "
            "caps=\"application/x-rtp, media=audio, clock-rate=8000, encoding-name=PCMU, payload=0\" "
            "! rtpbin.recv_rtp_sink_0 "
            "rtpbin. ! appsink name=appsink emit-signals=true sync=false"
        )

    def _attach_udp_port(self, pipeline, port):
        udpsrc = pipeline.get_by_name("udpsrc")
        udpsrc.set_property("port", port)

    def _attach_data_handler(self, pipeline):
        def on_new_sample(sink):
            sample = sink.emit('pull-sample')
            if sample:
                buf = sample.get_buffer()
                result, map_info = buf.map(Gst.MapFlags.READ)
                if result:
                    data = map_info.data
                    packet = PacketGenerator.generate_audio(len(data), data)
                    self.ws_client.send_audio_data(packet)
                    buf.unmap(map_info)
                return Gst.FlowReturn.OK
            return Gst.FlowReturn.ERROR

        appsink = pipeline.get_by_name("appsink")
        appsink.connect("new-sample", on_new_sample)

    def _run_loop(self):
        self.start_pipeline()
        while self.call_context.is_activate():
            time.sleep(1)
        self.pipeline.set_state(Gst.State.NULL)
        self.terminate()
        time.sleep(1)

    def terminate(self):
        try:
            self.logger.info(f"Terminating {self.__class__.__name__} of {self.call_context.callId}")
            self.ws_client.close()
        except Exception as e:
            pass
