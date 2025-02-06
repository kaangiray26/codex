import time
import aiohttp
from lib.helpers import get_env
from lib.models import Documents

# Daily REST API
from pipecat.transports.services.helpers.daily_rest import (
    DailyRESTHelper, DailyRoomParams, DailyRoomProperties
)

class ConnectionManager:
    def __init__(self):
        self.env = get_env()
        self.processes = dict()

        # Store sessions
        self.document: Documents

    def terminate_processes(self):
        for process in self.processes.values():
            process.terminate()
            process.wait()

    def add_process(self, pid, proc):
        self.processes[pid] = proc

    async def create_room_and_token(self) -> tuple[str, str]:
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            # Set Daily REST API helper
            helper = DailyRESTHelper(
                daily_api_key=self.env["DAILY_API_KEY"],
                daily_api_url="https://api.daily.co/v1",
                aiohttp_session=session,
            )

            # Create a room
            room = await helper.create_room(
                params=DailyRoomParams(
                    privacy="private",
                    properties=DailyRoomProperties(
                        enable_chat=True,
                        exp=time.time() + 1800
                    )
                )
            )

            # Generate a token for the room
            token = await helper.get_token(
                room_url=room.url,
                owner=True
            )
        return room.url, token