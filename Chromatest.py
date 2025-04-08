import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
# import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain_community.llms import OpenAI

import numpy as np
import pandas as pd
import matplotlib as mat
from tqdm import tqdm
import requests
import json
from langchain_community.document_loaders import PyPDFDirectoryLoader
from chromadb.config import Settings

# Load environment variables
load_dotenv()

# Set up OpenAI API
#openai.api_key = os.getenv("OPENAI_API_KEY")
#print(openai.api_key)

def read_doc(directory):
    file_loader = PyPDFDirectoryLoader(directory)
    documents=file_loader.load()
    return documents

orig_docs=read_doc('C:\\Users\\e1012814\\OneDrive - FIS\\Documents\\Innovate Data')
print(len(orig_docs))

# print(f"{pages[0].metadata}\n")
# print(pages[0].page_content)



def chunk_data(doc,chunk_size=800,chunk_overlap=50):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
    docs=text_splitter.split_documents(doc)
    return docs

chunk_docs=chunk_data(doc=orig_docs)
print(len(chunk_docs))


# from langchain_community.core.documents import BaseDocument

# # Assuming you have a BaseDocument instance
# document = BaseDocument(content="This is the content of the document.", metadata={"author": "John Doe"})

# # Convert the document to a string
# document_string = str(document.content)

# print(document_string)

ada_endpoint = "https://innovate-openai-api-mgt.azure-api.net/innovate-tracked/deployments/ada-002/embeddings?api-version=2024-02-01"
ada_api_key = "5525afe32ec74890a64807db7d7e871a"

ada_headers = {
    "Content-Type": "application/json",
    "api-key": ada_api_key
}

input_str= " "
ada_data = {
    "input": input_str,
    "model": "text-embedding-3-small"
}

def generate_embeddings(input_str):
    response = requests.post(ada_endpoint, headers=ada_headers, data=json.dumps(ada_data),verify=False)
    if response.status_code == 200:
       result = response.json()
       #print(result)
       return(result['data'][0]['embedding'])
   # else:
   #    print("failed")
   #    print(f"Error: {embed_docs.status_code}, {embed_docs.text}")
   

for chunks in chunk_docs:
    documents_str = str(chunks)
    embed_docs=generate_embeddings(documents_str)    

client = chromadb.Client(Settings())
collection_name = "innovate_collection"
collection = client.create_collection(name=collection_name)

for data in embed_docs:
    collection.add(data["embedding"])

# Load data into the collection
# for data in embedded_data:
#     collection.add(data["id"], data["embedding"], data["metadata"])

print(f"Added {len(embed_docs)} document chunks to the vector database.")

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


