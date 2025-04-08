import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain_community.llms import OpenAI
import json

import numpy as np
import pandas as pd
import matplotlib as mat
from tqdm import tqdm
import requests
import json
from langchain_community.document_loaders import PyPDFDirectoryLoader
from chromadb.config import Settings
import uuid

# Load environment variables
load_dotenv()

# Set up OpenAI API
#openai.api_key = os.getenv("OPENAI_API_KEY")
#print(openai.api_key)
directory = 'E:\\Programs\\Project\\Innovate Data'

ada_endpoint = "https://innovate-openai-api-mgt.azure-api.net/innovate-tracked/deployments/ada-002/embeddings?api-version=2024-02-01"
ada_api_key = "5525afe32ec74890a64807db7d7e871a"

ada_headers = {
    "Content-Type": "application/json",
    "api-key": ada_api_key
}

input_list= []
ada_data = {
    "input": input_list,
    "model": "text-embedding-3-small"
}

input_str= " "
ada_data_str = {
    "input": input_str,
    "model": "text-embedding-3-small"
}

def generate_embeddings(input_list):
    response = requests.post(ada_endpoint, headers=ada_headers, data=json.dumps(ada_data),verify=False)
    if response.status_code == 200:
       result = response.json()
       print(result)
       return(result['data'][0]['embedding'])
   # else:
   #    print("failed")
   #    print(f"Error: {embed_docs.status_code}, {embed_docs.text}")

def generate_embeddings_str(input_str):
    response = requests.post(ada_endpoint, headers=ada_headers, data=json.dumps(ada_data_str),verify=False)
    if response.status_code == 200:
       result = response.json()
       #print(result)
       return(result['data'][0]['embedding'])

chroma_client = chromadb.PersistentClient(path="chroma_persistent_storage")
collection_name = "document_qa_collection"
collection = chroma_client.get_or_create_collection(
    name=collection_name
)
       
#client = chromadb.Client(Settings())
#collection_name = "innovate_collection"
#client.delete_collection(name="innovate_collection")
#collection = client.create_collection(name=collection_name)
#print(type(chunk_docs))
#documents = [chunk.page_content if hasattr(chunk, 'page_content') else str(chunk) for chunk in chunk_docs]
#print(documents)
# Generate embeddings for the extracted text content
#embed_docs = generate_embeddings(chunk_docs)

def read_doc(directory):
    file_loader = PyPDFDirectoryLoader(directory)
    documents=file_loader.load()
    return documents

txt_documents = []
for filename in os.listdir(directory):
    if filename.endswith('.txt'):
        with open(os.path.join(directory, filename), 'r') as file:
            txt_documents.append({"id": filename, "text":file.read()})

print(txt_documents)

def split_text(text, chunk_size=1000, chunk_overlap=20):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks

chunked_documents = []
for doc in txt_documents:
    chunks = split_text(doc["text"])
    print("==== Splitting docs into chunks ====")
    for i, chunk in enumerate(chunks):
        chunked_documents.append({"id": f"{doc['id']}_chunk{i+1}", "text": chunk})


for doc in chunked_documents:
    print("==== Generating embeddings... ====")
    doc["embedding"] = generate_embeddings_str(doc["text"])

for doc in chunked_documents:
    print("==== Inserting chunks into db;;; ====")
    collection.upsert(
        ids=[doc["id"]], documents=[doc["text"]], embeddings=[doc["embedding"]]
    )

def query_documents(question, n_results=2):
    # query_embedding = get_openai_embedding(question)
    results = collection.query(query_texts=question, n_results=n_results)
     # Extract the relevant chunks
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    print("==== Returning relevant chunks ====")
    return relevant_chunks
#orig_docs=read_doc('E:\\Programs\\Project\\Innovate Data')
#metadata=[{"source": chunk_docs, "chunk-index": i} for i in range(len(chunk_docs))]

#print(len(orig_docs))

# print(f"{pages[0].metadata}\n")
# print(pages[0].page_content)

# def chunk_data(doc,chunk_size=800,chunk_overlap=50):
#     text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
#     docs=text_splitter.split_documents(doc)
#     print(type(docs))
#     for page in docs.pages:
#         doc_str = page.extract_text()
#         print(doc_str)

#     return doc_str

# chunk_docs=chunk_data(doc=orig_docs)
# print(len(chunk_docs))


# from langchain_community.core.documents import BaseDocument

# # Assuming you have a BaseDocument instance
# document = BaseDocument(content="This is the content of the document.", metadata={"author": "John Doe"})

# # Convert the document to a string
# document_string = str(document.content)

# print(document_string)

# ada_endpoint = "https://innovate-openai-api-mgt.azure-api.net/innovate-tracked/deployments/ada-002/embeddings?api-version=2024-02-01"
# ada_api_key = "5525afe32ec74890a64807db7d7e871a"

# ada_headers = {
#     "Content-Type": "application/json",
#     "api-key": ada_api_key
# }

# input_list= []
# ada_data = {
#     "input": input_list,
#     "model": "text-embedding-3-small"
# }

# input_str= " "
# ada_data_str = {
#     "input": input_str,
#     "model": "text-embedding-3-small"
# }

# def generate_embeddings(input_list):
#     response = requests.post(ada_endpoint, headers=ada_headers, data=json.dumps(ada_data),verify=False)
#     if response.status_code == 200:
#        result = response.json()
#        print(result)
#        return(result['data'][0]['embedding'])
#    # else:
#    #    print("failed")
#    #    print(f"Error: {embed_docs.status_code}, {embed_docs.text}")

# def generate_embeddings_str(input_str):
#     response = requests.post(ada_endpoint, headers=ada_headers, data=json.dumps(ada_data_str),verify=False)
#     if response.status_code == 200:
#        result = response.json()
#        #print(result)
#        return(result['data'][0]['embedding'])
       
# client = chromadb.Client(Settings())
# collection_name = "innovate_collection"
# #client.delete_collection(name="innovate_collection")
# collection = client.create_collection(name=collection_name)
# print(type(chunk_docs))
# #documents = [chunk.page_content if hasattr(chunk, 'page_content') else str(chunk) for chunk in chunk_docs]
# #print(documents)
# # Generate embeddings for the extracted text content
# embed_docs = generate_embeddings(chunk_docs)

#metadata = [{"source": chunk.metadata if hasattr(chunk, 'metadata') else {}, "chunk-index": i} for i, chunk in enumerate(chunk_docs)]

#import json  # Import json for serialization

# Generate metadata and ensure all values are serialized to strings
# metadata = [
#     {
#         "source": doc_str,  # Serialize metadata to JSON string
#         "chunk-index": i
#     }
#     for i, chunk in enumerate(chunk_docs)
# ]

# # Add the documents, embeddings, and metadata to the collection
# ids = [str(uuid.uuid4()) for _ in range(len(chunk_docs))]
# metadata=[{"source": chunk_docs, "chunk-index": i} for i in range(len(chunk_docs))]
# collection.add(ids=ids, documents=chunk_docs, embeddings=embed_docs, metadatas=metadata)

# print(f"Added document chunks to the vector database.")

# #embed_docs=generate_embeddings(chunk_docs)  

# for chunks in chunk_docs:
#     documents_str = str(chunks)
#     embed_docs=generate_embeddings(documents_str)  
    
# ids=[str(uuid.uuid4()) for _ in range(len(chunk_docs))]
# collection.add(ids=ids, documents=chunk_docs, embeddings=embed_docs, metadatas=metadata)

# for element in embed_docs:
#     collection.add(str(element))

# for data in embed_docs:
#     collection.add(data["embedding"])

# Load data into the collection
# for data in embedded_data:
#     collection.add(data["id"], data["embedding"], data["metadata"])

#print(f"Added {len(embed_docs)} document chunks to the vector database.")

# def query_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
#         """Query the vector database and get an AI-generated response."""
#         # Get embedding for the query
#         query_embedding = self._get_embedding(query)
        
#         # Search for similar documents
#         results = self.collection.query(
#             query_embeddings=[query_embedding],
#             n_results=n_results,
#             include=["documents", "metadatas", "distances"]
#         )
        
#         # Extract retrieved documents
#         retrieved_docs = results["documents"][0]
#         retrieved_metadatas = results["metadatas"][0]
        
#         # Format retrieved context
#         context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(retrieved_docs)])
    

# print(len(embed_docs))



# df_data={"col1": embed_docs}
# df=pd.DataFrame(df_data)
# print(df.head())
   
# import numpy as np

# def cosine_similarity(a, b):
#     sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
#     print(a, b)
#     print("sim=", sim)
#     return(sim)

# # Function to search documents
# def search_docs(df, user_query, top_n=4):
#     embedding = generate_embeddings(user_query)
#     print(embedding)
#     df["similarities"] = df["embedding_column"].apply(lambda x: cosine_similarity(x, embedding))
#     return df.sort_values("similarities", ascending=False).head(top_n)

# # Example usage
# import pandas as pd

# # Assuming df_bills is a DataFrame with document embeddings
# df_bills = pd.DataFrame({
#      "text": ["Document 1", "Document 2"],
#      "embedding_column": [generate_embeddings("Document 1"), generate_embeddings("Document 2")]
# })
# print(df_bills.head())

# query = "how are you?"
# results = search_docs(df_bills, query)
# print(results)

# from langchain.chains.question_answering import load_qa_chain
# from langchain import OpenAI

# # llm=OpenAI(model_name="text-embedding-3-small",temperature=0.5)
# # chain=load_qa_chain(llm,chain_type="stuff")

#Search answers from Vector DB
# def retrieve_answers(query):
#     doc_search=retrieve_query(query)
#     print(doc_search)
#     response=chain.run(input_documents=doc_search,question=query)
#     return(response)


