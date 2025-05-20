from submodules import Submodule

import logging
from util.aiohttp_utils import WSSender
from asyncio import sleep, get_running_loop, DatagramProtocol
from typing import Callable


class Antenna(Submodule):
    """
    Tracking Antenna submodule.
    """

    LOG = logging.getLogger(__name__)
    name = "antenna"
    data_provider: Callable[[None], str | None] = None

    def __init__(
        self, ws_sender: WSSender, data_provider: Callable[[None], str | None]
    ):
        super().__init__(None, ws_sender)
        self.data_provider = data_provider

    def handle_ws_msg(self, ws_data):
        pass

    async def send_udp_message_task(self):
        self.LOG.info("Starting UDP message sender task")
        while True:
            try:
                last_sat = self.data_provider()
                if last_sat:
                    await self.send_udp_message(last_sat)
                await sleep(1)
            except Exception as e:
                self.LOG.error(f"Error in UDP message sender task: {e}", exc_info=True)

    async def send_udp_message(self, message, host="127.0.0.1", port=42069):
        loop = get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: DatagramProtocol(), remote_addr=(host, port)
        )
        try:
            transport.sendto(message.encode())
        finally:
            transport.close()
