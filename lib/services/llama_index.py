import os

# Llama Index
from llama_index.core.query_engine import (
    RetrieverQueryEngine
)
from llama_index.core import (
    StorageContext, load_index_from_storage,
    get_response_synthesizer
)
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
)

# Pipecat
from llama_index.core.response_synthesizers import ResponseMode
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.services.ai_services import LLMService
from pipecat.processors.frame_processor import (
    FrameDirection
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

class LlamaIndexService(LLMService):
    def __init__(
        self,
        document_id: str,
        **kwargs
    ):
        super().__init__(**kwargs)
        # Load up the index from storage
        if not os.path.exists("storage"):
            raise Exception("Index not found!")
        self.index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="storage"),
            index_id="vector_index"
        )

        # Create query engine
        filters = self.create_filter_for_id(document_id)
        retriever = self.index.as_retriever(
            filters=filters
        )
        response_synthesizer = get_response_synthesizer(
            streaming=True,
            response_mode=ResponseMode.REFINE
        )
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        print("Query engine created!")

    def create_filter_for_id(self, document_id):
        return MetadataFilters(
            filters=[
                MetadataFilter(key="id_", value=document_id)
            ]
        )

    def can_generate_metrics(self) -> bool:
        return False

    async def _process_context(self, context: OpenAILLMContext):
        if not context.messages:
            return

        print("Processing context...")
        message = context.messages[-1].get("content")
        stream_response = await self.query_engine.aquery(message)
        async for token in stream_response.response_gen:
            await self.push_frame(TextFrame(token))

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        context = None
        if isinstance(frame, OpenAILLMContextFrame):
            context: OpenAILLMContext = frame.context
        elif isinstance(frame, LLMMessagesFrame):
            context = OpenAILLMContext.from_messages(frame.messages)
        else:
            await self.push_frame(frame, direction)

        if context:
            await self.push_frame(LLMFullResponseStartFrame())
            await self._process_context(context)
            await self.push_frame(LLMFullResponseEndFrame())

    def _estimate_tokens(self, text: str) -> int:
        return 1