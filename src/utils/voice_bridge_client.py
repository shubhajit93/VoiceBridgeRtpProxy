import websocket
import threading


class VoiceBridgeClient:
    def __init__(self, uri, on_message_callback):
        self.thread = None
        self.uri = uri
        self.on_message_callback = on_message_callback
        self.websocket = None
        self.connect()

    def connect(self):
        self.websocket = websocket.WebSocketApp(
            self.uri,
            on_message=self.on_message,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error
        )
        self.thread = threading.Thread(target=self.websocket.run_forever)
        self.thread.daemon = True
        self.thread.start()

    def on_open(self, ws):
        print("WebSocket connection opened")

    def on_message(self, ws, message):
        self.on_message_callback(message)

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def send_audio_data(self, audio_data):
        if self.websocket:
            self.websocket.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)

    def close(self):
        if self.websocket:
            self.websocket.close()
