from pydantic import BaseModel
from typing import Any, List, Optional, Sequence

from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.response.schema import RESPONSE_TYPE
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.indices.base import BaseGPTIndex
from llama_index.core.llms.llm import LLM
from llama_index.core.node_parser import SentenceSplitter, TextSplitter
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.base import BasePromptTemplate
from llama_index.core.prompts.mixin import PromptMixinType
from llama_index.core.response_synthesizers import (
    BaseSynthesizer,
    ResponseMode,
    get_response_synthesizer,
)
from llama_index.core.schema import (
    MetadataMode,
    NodeWithScore,
    QueryBundle,
    TextNode,
)
from llama_index.core.settings import Settings

qa_prompt = PromptTemplate(
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the query. And provide a list of sources used in the answer.\n"
)

CITATION_QA_TEMPLATE = PromptTemplate(
    "Please provide an answer based solely on the provided sources. "
    "You response consists of the answer and the citations. "
    "When referencing information from a source, add their corresponding numbers to the citations list in the output. "
    "Every answer should include at least one source citation. "
    "Only cite a source when you are explicitly referencing it. "
    "If none of the sources are helpful, you should indicate that. "
    "For example:\n"
    "Source 1:\n"
    "The sky is red in the evening and blue in the morning.\n"
    "Source 2:\n"
    "Water is wet when the sky is red.\n"
    "Query: When is water wet?\n"
    "Answer: Water will be wet when the sky is red, "
    "which occurs in the evening.\n"
    "Citations: [2, 1]\n"
    "Now it's your turn. Below are several numbered sources of information:"
    "\n------\n"
    "{context_str}"
    "\n------\n"
    "Query: {query_str}\n"
    "Answer: "
)

DEFAULT_CITATION_CHUNK_SIZE = 512
DEFAULT_CITATION_CHUNK_OVERLAP = 20

class CitatedAnswer(BaseModel):
    answer: str
    citations: List[int]

class CitatedQueryEngine(BaseQueryEngine):
    def __init__(
        self,
        retriever: BaseRetriever,
        llm: Optional[LLM] = None,
        response_synthesizer: Optional[BaseSynthesizer] = None,
        citation_chunk_size: int = DEFAULT_CITATION_CHUNK_SIZE,
        citation_chunk_overlap: int = DEFAULT_CITATION_CHUNK_OVERLAP,
        text_splitter: Optional[TextSplitter] = None,
        node_postprocessors: Optional[List[BaseNodePostprocessor]] = None,
        callback_manager: Optional[CallbackManager] = None,
        metadata_mode: MetadataMode = MetadataMode.NONE,
    ) -> None:
        self.text_splitter = text_splitter or SentenceSplitter(
            chunk_size=citation_chunk_size, chunk_overlap=citation_chunk_overlap
        )
        self._retriever = retriever

        callback_manager = callback_manager or Settings.callback_manager
        llm = llm or Settings.llm

        self._response_synthesizer = response_synthesizer or get_response_synthesizer(
            llm=llm,
            callback_manager=callback_manager,
        )
        self._node_postprocessors = node_postprocessors or []
        self._metadata_mode = metadata_mode

        for node_postprocessor in self._node_postprocessors:
            node_postprocessor.callback_manager = callback_manager

        super().__init__(callback_manager=callback_manager)

    @classmethod
    def from_args(
        cls,
        index: BaseGPTIndex,
        llm: Optional[LLM] = None,
        response_synthesizer: Optional[BaseSynthesizer] = None,
        citation_chunk_size: int = DEFAULT_CITATION_CHUNK_SIZE,
        citation_chunk_overlap: int = DEFAULT_CITATION_CHUNK_OVERLAP,
        text_splitter: Optional[TextSplitter] = None,
        citation_qa_template: BasePromptTemplate = CITATION_QA_TEMPLATE,
        retriever: Optional[BaseRetriever] = None,
        node_postprocessors: Optional[List[BaseNodePostprocessor]] = None,
        # response synthesizer args
        response_mode: ResponseMode = ResponseMode.COMPACT,
        use_async: bool = False,
        streaming: bool = False,
        # class-specific args
        metadata_mode: MetadataMode = MetadataMode.NONE,
        **kwargs: Any,
    ) -> "CitatedQueryEngine":
        retriever = retriever or index.as_retriever(**kwargs)

        response_synthesizer = response_synthesizer or get_response_synthesizer(
            llm=llm,
            text_qa_template=citation_qa_template,
            response_mode=response_mode,
            use_async=use_async,
            streaming=streaming,
            output_cls=CitatedAnswer,
        )

        return cls(
            retriever=retriever,
            llm=llm,
            response_synthesizer=response_synthesizer,
            callback_manager=Settings.callback_manager,
            citation_chunk_size=citation_chunk_size,
            citation_chunk_overlap=citation_chunk_overlap,
            text_splitter=text_splitter,
            node_postprocessors=node_postprocessors,
            metadata_mode=metadata_mode,
        )

    def _get_prompt_modules(self) -> PromptMixinType:
        """Get prompt sub-modules."""
        return {"response_synthesizer": self._response_synthesizer}

    def _create_citation_nodes(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """Modify retrieved nodes to be granular sources."""
        new_nodes: List[NodeWithScore] = []
        for node in nodes:
            text_chunks = self.text_splitter.split_text(
                node.node.get_content(metadata_mode=self._metadata_mode)
            )

            for text_chunk in text_chunks:
                text = f"Source {len(new_nodes) + 1}:\n{text_chunk}\n"

                new_node = NodeWithScore(
                    node=TextNode.model_validate(node.node.model_dump()),
                    score=node.score,
                )
                new_node.node.set_content(text)
                new_nodes.append(new_node)
        return new_nodes

    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = self._retriever.retrieve(query_bundle)

        for postprocessor in self._node_postprocessors:
            nodes = postprocessor.postprocess_nodes(nodes, query_bundle=query_bundle)

        return nodes

    async def aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = await self._retriever.aretrieve(query_bundle)

        for postprocessor in self._node_postprocessors:
            nodes = postprocessor.postprocess_nodes(nodes, query_bundle=query_bundle)

        return nodes

    @property
    def retriever(self) -> BaseRetriever:
        """Get the retriever object."""
        return self._retriever

    def synthesize(
        self,
        query_bundle: QueryBundle,
        nodes: List[NodeWithScore],
        additional_source_nodes: Optional[Sequence[NodeWithScore]] = None,
    ) -> RESPONSE_TYPE:
        nodes = self._create_citation_nodes(nodes)
        return self._response_synthesizer.synthesize(
            query=query_bundle,
            nodes=nodes,
            additional_source_nodes=additional_source_nodes,
        )

    async def asynthesize(
        self,
        query_bundle: QueryBundle,
        nodes: List[NodeWithScore],
        additional_source_nodes: Optional[Sequence[NodeWithScore]] = None,
    ) -> RESPONSE_TYPE:
        nodes = self._create_citation_nodes(nodes)
        return await self._response_synthesizer.asynthesize(
            query=query_bundle,
            nodes=nodes,
            additional_source_nodes=additional_source_nodes,
        )

    def _query(self, query_bundle: QueryBundle) -> RESPONSE_TYPE:
        """Answer a query."""
        with self.callback_manager.event(
            CBEventType.QUERY, payload={EventPayload.QUERY_STR: query_bundle.query_str}
        ) as query_event:
            with self.callback_manager.event(
                CBEventType.RETRIEVE,
                payload={EventPayload.QUERY_STR: query_bundle.query_str},
            ) as retrieve_event:
                nodes = self.retrieve(query_bundle)
                nodes = self._create_citation_nodes(nodes)

                retrieve_event.on_end(payload={EventPayload.NODES: nodes})

            response = self._response_synthesizer.synthesize(
                query=query_bundle,
                nodes=nodes,
            )

            query_event.on_end(payload={EventPayload.RESPONSE: response})

        return response

    async def _aquery(self, query_bundle: QueryBundle) -> RESPONSE_TYPE:
        """Answer a query."""
        with self.callback_manager.event(
            CBEventType.QUERY, payload={EventPayload.QUERY_STR: query_bundle.query_str}
        ) as query_event:
            with self.callback_manager.event(
                CBEventType.RETRIEVE,
                payload={EventPayload.QUERY_STR: query_bundle.query_str},
            ) as retrieve_event:
                nodes = await self.aretrieve(query_bundle)
                nodes = self._create_citation_nodes(nodes)

                retrieve_event.on_end(payload={EventPayload.NODES: nodes})

            response = await self._response_synthesizer.asynthesize(
                query=query_bundle,
                nodes=nodes,
            )

            query_event.on_end(payload={EventPayload.RESPONSE: response})

        return response