from typing import Optional, List

from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from lib.helpers import get_env
from lib.models import Environment

# Pipeline
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

# Transport
from pipecat.transports.services.daily import DailyTransport, DailyParams

# Services
from pipecat.transcriptions.language import Language
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.openai import OpenAILLMService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.elevenlabs import ElevenLabsTTSService

# Processor
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.processors.frameworks.rtvi import (
    RTVIConfig, RTVIProcessor, RTVISpeakingProcessor,
    RTVIUserTranscriptionProcessor, RTVIBotTranscriptionProcessor
)
# from lib.processors.llama_index import LLamaIndexProcessor
from lib.services.llama_index import LlamaIndexService

# Filters
from pipecat.processors.filters.stt_mute_filter import (
    STTMuteFilter,
    STTMuteConfig,
    STTMuteStrategy,
)

# All frames
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContextFrame
from pipecat.frames.frames import (
    TranscriptionMessage, TranscriptionUpdateFrame
)

class TranscriptHandler:
    def __init__(self):
        self.messages: List[TranscriptionMessage] = []

    async def on_transcript_update(self, processor: TranscriptProcessor, frame: TranscriptionUpdateFrame):
        for msg in frame.messages:
            self.messages.append(msg)
            await self.handle_message(msg)

    async def handle_message(self, message: TranscriptionMessage):
        print(f"Transcript: {message.role}: {message.content}")

class Bot:
    def __init__(self, url, token, document_id):
        self.url = url
        self.token = token
        self.document_id = document_id
        self.env: Environment = get_env()

        # Variables
        self.task: Optional[PipelineTask] = None
        self.runner: Optional[PipelineRunner] = None

        # Configure services
        self.stt = DeepgramSTTService(
            api_key=self.env["DEEPGRAM_API_KEY"]
        )

        self.tts = ElevenLabsTTSService(
            api_key=self.env["ELEVENLABS_API_KEY"],
            voice_id="aEO01A4wXwd1O8GPgGlF",
            stability=0.5,
            params=ElevenLabsTTSService.InputParams(
                language=Language.EN_US
            )
        )

        self.llm = LlamaIndexService(
            document_id=self.document_id
        )

        # Aggregator
        context = OpenAILLMContext(
            messages=[{
                "role": "system",
                "content": "You are Codex, an AI assistant. Your goal is to answer questions about the document. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in an informative and helpful way, but keep your responses brief. Start by introducing yourself."
            }]
        )
        self.context_aggregator = OpenAILLMService.create_context_aggregator(context)

        # STT mute filter
        self.stt_mute_filter = STTMuteFilter(
            stt_service=self.stt,
            config=STTMuteConfig(strategies={STTMuteStrategy.ALWAYS})
        )

        # Initialize RTVI with default config
        self.rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
        self.rtvi_speaking = RTVISpeakingProcessor()
        self.rtvi_user_transcription = RTVIUserTranscriptionProcessor()
        self.rtvi_bot_transcription = RTVIBotTranscriptionProcessor()

    # Configure transport
    async def create_transport(self):
        self.transport = DailyTransport(
            room_url=self.url,
            token=self.token,
            bot_name="Codex",
            params=DailyParams(
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
            )
        )

        # Event handlers
        @self.transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            if not self.task:
                return

            # Create welcome message
            print("Sending welcome message...")
            await self.task.queue_frames([self.context_aggregator.user().get_context_frame()])

        @self.transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            print("Participant left:", participant, reason)
            if not self.task:
                return
            await self.task.cancel()
            
            # End the pipeline
            exit()

    async def create_pipeline(self):
        if not self.transport:
            raise Exception("Transport not ready!")

        # Use in pipeline
        pipeline = Pipeline([
            self.transport.input(),
            self.stt_mute_filter,
            self.rtvi_speaking,
            self.stt,
            self.rtvi_user_transcription,
            self.context_aggregator.user(),
            self.llm,
            self.rtvi_bot_transcription,
            self.tts,
            self.transport.output(),
            self.context_aggregator.assistant(),
        ])

        self.task = PipelineTask(
            pipeline,
            PipelineParams(
                allow_interruptions=True,
                observers=[self.rtvi.observer()],
            )
        )
        self.runner = PipelineRunner()

    async def start(self):
        # Check the runner and task
        if not self.runner or not self.task:
            raise Exception("Bot not ready!")

        # Run the task
        await self.runner.run(self.task)