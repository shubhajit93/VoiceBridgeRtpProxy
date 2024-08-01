from fastapi import FastAPI
import uvicorn
from src.server.base import RtpProxyServer
import logging

app = FastAPI()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Add the console handler to the logger
# logger.addHandler(console_handler)

server = RtpProxyServer(
    logger=logger
)


def main():
    print("Server is starting...")
    app.include_router(server.get_router())
    uvicorn.run(app, host="0.0.0.0", port=3002)


if __name__ == "__main__":
    main()
