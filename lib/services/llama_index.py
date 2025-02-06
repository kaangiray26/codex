import os
from pydantic import BaseModel
from typing import Literal, Dict, Any

# Llama Index
from llama_index.core.query_engine import (
    CitationQueryEngine
)
from llama_index.core import (
    StorageContext,
    load_index_from_storage
)
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
)

# Pipecat
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.services.ai_services import LLMService
from pipecat.processors.frame_processor import (
    FrameDirection
)
from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    LLMTextFrame
)
from pipecat.processors.frameworks.rtvi import (
    TransportMessageUrgentFrame,
    RTVIMessageLiteral, RTVI_MESSAGE_LABEL
)
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

# Set the llm model
Settings.llm = OpenAI(
    model="gpt-4",
    temperature=0.5,
)

class RTVICitationsMessage(BaseModel):
    label: RTVIMessageLiteral = RTVI_MESSAGE_LABEL
    type: Literal["citations"] = "citations"
    data: Dict[str, Any]

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
        self.query_engine = CitationQueryEngine.from_args(
            index=self.index,
            similarity_top_k=3,
            retriever=retriever,
            citation_chunk_size=256,
            streaming=True
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

        message = context.messages[-1].get("content")

        citations = []
        getting_citation = False

        # Query the engine
        streaming_response = await self.query_engine.aquery(message)
        async for response in streaming_response.response_gen:
            text = response.strip()
            if not len(text):
                continue

            if text.startswith("["):
                getting_citation = True
                continue

            if text.startswith("]"):
                getting_citation = False
                await self.push_frame(LLMTextFrame(". "))
                continue

            if getting_citation:
                citations.append(int(text))
                continue

            await self.push_frame(LLMTextFrame(response))
            getting_citation = False

        # Return the citations
        model = RTVICitationsMessage(
            data={
                "sources": [streaming_response.source_nodes[i-1].node.text for i in citations]
            }
        )
        await self.push_frame(
            TransportMessageUrgentFrame(message=model.model_dump()),
            FrameDirection.DOWNSTREAM
        )

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