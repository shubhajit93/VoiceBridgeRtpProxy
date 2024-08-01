import threading
from typing import Optional

class ThreadAsyncWorker:
    def __init__(
            self
    ) -> None:
        self.worker_thread: Optional[threading.Thread] = None

    def start(self):
        self.worker_thread = threading.Thread(target=self._run_loop)
        self.worker_thread.start()

    def _run_loop(self):
        raise NotImplementedError

    def terminate(self):
        raise NotImplementedError
