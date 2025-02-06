import os
from loguru import logger
from typing import Optional
from markitdown import MarkItDown

# Llama Index
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.indices.base import BaseIndex
from llama_index.core import (
    VectorStoreIndex, Document,
    StorageContext, load_index_from_storage
)

# Pipecat
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContextFrame
from pipecat.services.ai_services import LLMService
from pipecat.processors.frame_processor import (
    FrameDirection, FrameProcessor
)
from pipecat.frames.frames import (
    StartFrame,
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    TextFrame,
    TTSSpeakFrame
)

class LLamaIndexProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()

        # Create a markdown parser
        self.md = MarkItDown()

        # Parser
        self.parser = SentenceSplitter()

        # Create index
        self.index: Optional[BaseIndex] = None

        # Create storage context
        self.storage_context = None

        # Check if we have persisted storage
        if not os.path.exists("storage"):
            raise Exception("Index not found!")
        self.index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="storage"),
            index_id="vector_index"
        )

        # Create chat engine
        self.query_engine = self.index.as_query_engine()
        print("Chat engine created!")

    def set_participant_id(self, participant_id: str):
        self._participant_id = participant_id

    def create_index(self):
        self.index = VectorStoreIndex.from_documents([])
        self.index.set_index_id("vector_index")
        self.index.storage_context.persist("./storage")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Process the start frame
        if isinstance(frame, StartFrame):
            await self.push_frame(LLMFullResponseStartFrame())
            await self.push_frame(TTSSpeakFrame("Hello! I am Codex. What do you want to ask about the document?"))
            await self.push_frame(LLMFullResponseEndFrame())
            return

        # Process the messages frame
        if isinstance(frame, OpenAILLMContextFrame):
            print(f"Got frame {frame}")
            print(f"Messages: {frame.context.messages}")
            text: str = frame.context.messages[-1]["content"]
            await self._ainvoke(text.strip())
            return

        # Otherwise, push the frame
        await self.push_frame(frame, direction)

    async def _ainvoke(self, text: str):
        await self.push_frame(LLMFullResponseStartFrame())
        print("Asking question:", text)
        try:
            response = self.query_engine.query(text)
            await self.push_frame(TextFrame(response))
        except GeneratorExit:
            print(f"{self} generator was closed prematurely")
        except Exception as e:
            print(f"{self} an unknown error occurred: {e}")
        finally:
            await self.push_frame(LLMFullResponseEndFrame())