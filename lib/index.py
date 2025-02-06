import os
import time
from typing import Optional
from markitdown import MarkItDown
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.indices.base import BaseIndex
from llama_index.core import (
    VectorStoreIndex, Document,
    StorageContext, load_index_from_storage
)

class LlamaIndex:
    def __init__(self):
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
            self.create_index()
            return

        # Load the index from storage
        self.index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="storage"),
            index_id="vector_index"
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

        # Parse nodes
        nodes = self.parser.get_nodes_from_documents(documents)
        self.index = VectorStoreIndex(nodes)

    def add_document_to_index(self, document_id):
        # Check if we have an index
        if not self.index:
            raise Exception("Index not found!")

        path = os.path.join("uploads", document_id)
        documents = self.parse_with_markitdown(document_id, path)

        # Parse nodes
        nodes = self.parser.get_nodes_from_documents(documents)
        self.index.insert_nodes(nodes)

        # Save index to disk
        self.index.set_index_id("vector_index")
        self.index.storage_context.persist("./storage")

    def parse_with_markitdown(self, document_id, file_path) -> list[Document]:
        # Parse the pdf
        result = self.md.convert(file_path)

        # Create documents
        return [
            Document(
                doc_id=document_id,
                text=result.text_content
            )
        ]

    def answer(self, query, document_id):
        print(f"Answering question: {query}")
        if not self.index:
            raise Exception("Index not found!")

        # Query the index
        start = time.time()
        query_engine = self.index.as_query_engine()
        end = time.time()
        response = query_engine.query(query)
        print(f"Query took: {end - start :.2f} seconds")
        print(response)


if __name__ == "__main__":
    from lib.helpers import set_env
    # Load the config
    set_env()

    index = LlamaIndex()

    # Ask a question
    index.answer(
        query = "would a daughter of a friend revive a correlative idea? If yes, please explain why.",
        document_id = "12984e0a4e8de38774feb40197952242c4f240cbb93fac69ab7d8aa77e7e37be"
    )