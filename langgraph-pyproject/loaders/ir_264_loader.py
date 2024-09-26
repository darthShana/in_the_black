import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_voyageai import VoyageAIEmbeddings

file_path = "loaders/IR264_2024.pdf"
loader = PyPDFLoader(file_path)

docs = loader.load()

print(len(docs))
print(docs[7].page_content[0:500])
print(docs[7].metadata)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

embeddings = VoyageAIEmbeddings(voyage_api_key=os.environ["VOYAGE_API_KEY"], model="voyage-large-2")
vectorstore = PineconeVectorStore.from_documents(docs, embeddings, index_name="ir264-2024")
