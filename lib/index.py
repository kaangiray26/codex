import os
from typing import Optional
from markitdown import MarkItDown

from llama_index.core.indices.base import BaseIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import (
    VectorStoreIndex, Document,
    StorageContext, load_index_from_storage,
)
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters
)

class LlamaIndex:
    def __init__(self):
        # Create a markdown parser
        self.md = MarkItDown()

        # Parser
        self.parser = SentenceSplitter()

        # Create index
        self.index: Optional[BaseIndex] = None
        self.query_engine: Optional[BaseQueryEngine] = None
        self.chat_engine: Optional[CondenseQuestionChatEngine] = None

        # Create storage context
        self.storage_context = None

        # Check if we have persisted storage
        if not os.path.exists("storage"):
            self.create_index()
            return

        # Load the index from storage
        self.index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="storage"),
            index_id="vector_index"
        )

    def create_filter_by_id(self, document_id):
        return MetadataFilters(
            filters=[
                MetadataFilter(key="id_", value=document_id)
            ]
        )

    def create_index(self):
        print("Creating index...")
        self.index = VectorStoreIndex.from_documents([])
        self.index.set_index_id("vector_index")
        self.index.storage_context.persist("./storage")

    def create_index_from_document(self, document_id):
        # Parse the document
        path = os.path.join("uploads", document_id)
        documents = self.parse_with_markitdown(document_id, path)
        self.index = VectorStoreIndex.from_documents(documents)

    def add_document_to_index(self, document_id):
        # Check if we have an index
        if not self.index:
            raise Exception("Index not found!")

        path = os.path.join("uploads", document_id)
        documents = self.parse_with_markitdown(document_id, path)
        for doc in documents:
            self.index.insert(doc)

        # Refresh the index
        self.index.refresh(documents)

        # Save index to disk
        self.index.set_index_id("vector_index")
        self.index.storage_context.persist("./storage")
        print("Document added to index!")

    def parse_with_markitdown(self, document_id, file_path) -> list[Document]:
        # Parse the pdf
        result = self.md.convert(file_path)

        # Create documents
        return [
            Document(
                text=result.text_content,
                id_=document_id,
                metadata={"id_": document_id}
            )
        ]