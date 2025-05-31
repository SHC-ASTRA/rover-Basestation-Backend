from submodules import Submodule
import logging
from util.aiohttp_utils import WSSender
from asyncio import sleep, get_running_loop, DatagramProtocol
from typing import Callable
from util import websocket_types
from json import loads


class TrackingAntennaProtocol(DatagramProtocol):
    LOG = logging.getLogger(__name__)

    def __init__(self, ws_sender: WSSender):
        self.ws_sender = ws_sender

    def datagram_received(self, data, addr):
        loop = get_running_loop()
        msg = websocket_types.AntennaFeedbackData.from_dict(loads(data.decode()))
        self.LOG.debug(f"Received UDP from {addr}: {msg.to_json()}")
        loop.create_task(self.ws_sender.send(msg.to_json()))


class Antenna(Submodule):
    """
    Tracking Antenna submodule.
    """

    LOG = logging.getLogger(__name__)
    name = "antenna"
    data_provider: Callable[[None], str | None] = None
    overwrite_msg: str | None = None

    def __init__(
        self, ws_sender: WSSender, data_provider: Callable[[None], str | None]
    ):
        super().__init__(None, ws_sender)
        self.data_provider = data_provider
        self.udp_transport = None  # Will hold persistent transport for receiving

    def handle_ws_msg(self, ws_data):
        if isinstance(ws_data, websocket_types.AntennaResetData):
            self.overwrite_msg = ws_data.data["message"]
            return True
        return False

    async def send_udp_message_task(self):
        self.LOG.info("Starting UDP message sender task")
        while True:
            try:
                to_send = self.data_provider()
                if self.overwrite_msg is not None:
                    if self.overwrite_msg.startswith("!"):
                        to_send = self.overwrite_msg[1:]
                    else:
                        to_send = self.overwrite_msg
                        self.overwrite_msg = None
                if to_send:
                    await self.send_udp_message(to_send)
                await sleep(1)
            except Exception as e:
                self.LOG.error(f"Error in UDP message sender task: {e}", exc_info=True)

    async def send_udp_message(self, message, host="192.168.1.4", port=42069):
        loop = get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: TrackingAntennaProtocol(
                self.ws_sender
            ),  # No need to receive in this one-time send
            remote_addr=(host, port),
        )
        try:
            transport.sendto(message.encode())
        finally:
            transport.close()

    async def listen_for_udp_messages(self, local_host="0.0.0.0", local_port=42069):
        self.LOG.info(f"Listening for UDP on {local_host}:{local_port}")
        loop = get_running_loop()
        self.udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: TrackingAntennaProtocol(self.ws_sender),
            local_addr=(local_host, local_port),
        )
