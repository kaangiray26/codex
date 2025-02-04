from fastapi import WebSocket
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams
)


class ConnectionManager:
    def __init__(self):
        self.connections = set()

    async def connect(self, websocket: WebSocket) -> FastAPIWebsocketTransport:
        # Accept the incoming connection
        await websocket.accept()
        self.connections.add(websocket)
        
        # Configure transport
        return FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                serializer=ProtobufFrameSerializer(),
                audio_out_enabled=True,
                # TODO: Improvements
                # vad_enabled=True,
                # vad_analyzer=SileroVADAnalyzer(),
                # vad_audio_passthrough=True,
            )
        )