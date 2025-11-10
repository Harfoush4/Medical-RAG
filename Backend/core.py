from dotenv import load_dotenv
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain


load_dotenv()

from langchain_classic import hub
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from typing import List, Dict,Any, Tuple




def run_llm(query: str, chat_history: List[Tuple[str, str]] = []):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    docsearch = Chroma(persist_directory="D:\AI\Projects.2\documentation-helper\chroma_db", embedding_function=embeddings)
    chat = ChatOllama(model="gemma3:1b")


    retrievel_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(chat, retrievel_qa_chat_prompt)

    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm=chat, retriever=docsearch.as_retriever(),prompt=rephrase_prompt
    )



    qa = create_retrieval_chain(
        retriever=history_aware_retriever,combine_docs_chain=stuff_documents_chain,
    )
    result= qa.invoke(input={"input": query,"chat_history":chat_history})
    new_result={
        "query": result["input"],
        "result": result["answer"],
        "source_documents": result["context"],
    }
    return new_result

if __name__ == "__main__":
    res = run_llm(query="What is Langchain Chain?")
    print(res["result"])