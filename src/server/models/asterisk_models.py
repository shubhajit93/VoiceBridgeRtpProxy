import uuid
from enum import Enum, IntEnum
import logging


class PacketType(Enum):
    TERMINATE: bytes = b'\x00'
    UUID: bytes = b'\x01'
    PAYLOAD: bytes = b'\x10'
    SILENCE: bytes = b'\x02'
    ERROR: bytes = b'\xff'
    NONE: bytes = b'\x02'


class ErrorSpec(IntEnum):
    HANGUP_CALLING_PARTY = 0x01
    FRAME_FORWARDING_ERROR = 0x02
    MEMORY_ALLOCATION_ERROR = 0x04


class Packet:
    logger = logging.getLogger(__name__)

    def __init__(self, data: bytes) -> None:
        self._type: PacketType = PacketType.NONE
        self._payload_length: int = 0
        self._payload: bytes = b''
        self._uuid: str = ""

        if len(data) < 3:
            raise ValueError("Invalid packet length")

        # self._type = PacketType(data[0])
        try:
            self._type = PacketType(data[0:1])
        except ValueError as e:
            self._type = PacketType.NONE
            self.logger.warning("Invalid packet type: %s", e)
            pass

        if self._type == PacketType.UUID:
            if len(data) < 19:
                raise ValueError("Invalid UUID packet: insufficient data")
            self._uuid = str(uuid.UUID(bytes=data[3:19]))  # Convert UUID bytes to string
        elif self._type == PacketType.PAYLOAD or self._type == PacketType.ERROR:
            self._payload_length = int.from_bytes(data[1:3], byteorder='big')
            if self._payload_length < 160:
                print("Payload length: ", self._payload_length)
            if len(data) < 3 + self._payload_length:
                self.logger.warning("Invalid packet: insufficient payload data %s", data.decode('utf-8'))
            self._payload = data[3:3 + self._payload_length]
        elif self._type == PacketType.TERMINATE:
            self._has_terminate = True

        if self.has_error:
            error_code = int.from_bytes(data[1:3], byteorder='big')
            self.logger.warning("Asterisk error code %s", error_code)
            if error_code & ErrorSpec.HANGUP_CALLING_PARTY:
                self._error_spec = ErrorSpec.HANGUP_CALLING_PARTY
            elif error_code & ErrorSpec.FRAME_FORWARDING_ERROR:
                self._error_spec = ErrorSpec.FRAME_FORWARDING_ERROR
            elif error_code & ErrorSpec.MEMORY_ALLOCATION_ERROR:
                self._error_spec = ErrorSpec.MEMORY_ALLOCATION_ERROR

    @property
    def type(self) -> PacketType:
        return self._type

    @property
    def payload_length(self) -> int:
        return self._payload_length

    @property
    def payload(self) -> bytes:
        return self._payload

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def has_error(self) -> bool:
        return self._type == PacketType.ERROR

    @property
    def has_terminate(self) -> bool:
        return self._type == PacketType.TERMINATE

    @property
    def has_payload(self) -> bool:
        return self._type == PacketType.PAYLOAD

    @property
    def has_uuid(self) -> bool:
        return self._type == PacketType.UUID


class PacketGenerator:
    logger = logging.getLogger(__name__)

    @staticmethod
    def generate_audio(pcm_size: int, data: bytes):
        try:
            return PacketType.PAYLOAD.value + pcm_size.to_bytes(2, 'big') + data
        except Exception as e:
            PacketGenerator.logger.warning("Error generating audio packet: %s", e)
            return None

    @staticmethod
    def generate_terminate():
        return PacketType.TERMINATE.value * 3
