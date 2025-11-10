import os
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any, Optional
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic import hub
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

# Default settings
DEFAULT_CONFIG = {
    "model": "gemma3:1b",
    "temperature": 0.1,
    "k": 4,
    "chroma_path": r"D:/AI/Projects.2/RAG_Full_Power_1/chroma_db_doctora_async",
    "embedding_model": "nomic-embed-text",
}

# Cache for expensive operations
_vector_store_cache = None
_embeddings_cache = None


def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return DEFAULT_CONFIG.copy()


def get_embeddings(model: str = None) -> OllamaEmbeddings:
    """Get or create embeddings model (cached)."""
    global _embeddings_cache

    if model is None:
        model = DEFAULT_CONFIG["embedding_model"]

    if _embeddings_cache is None or _embeddings_cache.model != model:
        print(f"📊 Loading embeddings: {model}")
        _embeddings_cache = OllamaEmbeddings(model=model)

    return _embeddings_cache


def get_vector_store(embeddings: OllamaEmbeddings = None) -> Chroma:
    """Get or create vector store (cached)."""
    global _vector_store_cache

    if embeddings is None:
        embeddings = get_embeddings()

    if _vector_store_cache is None:
        print(f"💾 Loading vector store: {DEFAULT_CONFIG['chroma_path']}")
        _vector_store_cache = Chroma(
            persist_directory=DEFAULT_CONFIG["chroma_path"],
            embedding_function=embeddings
        )

    return _vector_store_cache


def validate_vector_store() -> bool:
    """Check if vector store has documents."""
    try:
        vector_store = get_vector_store()
        # Try a test query
        test_results = vector_store.similarity_search("test", k=1)
        return len(test_results) > 0
    except Exception as e:
        print(f"❌ Vector store validation failed: {e}")
        return False




# ============================================
# MAIN QUERY FUNCTION
# ============================================

def run_llm(
        query: str,
        chat_history: List[Tuple[str, str]] = None,
        model: str = None,
        temperature: float = None,
        k: int = None,
) -> Dict[str, Any]:
    """
    Run RAG query with conversation history and strict context grounding.

    Args:
        query: User's question
        chat_history: List of (role, message) tuples
        model: LLM model to use (default: gemma3:1b)
        temperature: Creativity (0-1, default: 0.7)
        k: Number of documents to retrieve (default: 4)

    Returns:
        Dict with 'query', 'result', and 'source_documents'
    """
    # Use defaults if not provided
    if chat_history is None:
        chat_history = []
    if model is None:
        model = DEFAULT_CONFIG["model"]
    if temperature is None:
        temperature = DEFAULT_CONFIG["temperature"]
    if k is None:
        k = DEFAULT_CONFIG["k"]

    print(f"\n{'=' * 60}")
    print(f"🔍 Query: {query}")
    print(f"📚 Model: {model} | Temp: {temperature} | K: {k}")
    print(f"💬 Chat history: {len(chat_history)} messages")
    print(f"{'=' * 60}\n")

    try:
        # Get components
        embeddings = get_embeddings()
        vector_store = get_vector_store(embeddings)

        # Initialize LLM
        chat = ChatOllama(
            model=model,
            temperature=temperature
        )

        # ============================================
        # CUSTOM STRICT PROMPT - ENFORCES CONTEXT ONLY
        # ============================================
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        retrieval_qa_chat_prompt = ChatPromptTemplate.from_messages([
            ("system", """

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:

1. Answer questions ONLY using the provided context below
2. If the context does not contain the answer, respond with: "I don't have that information in my database. "
3. NEVER use your general knowledge or training data to answer questions
4. Only cite information that is explicitly stated in the context
5. If you're unsure or the information is incomplete, say so clearly

Context:
{context}

Remember: If the answer is not in the context above, you MUST say you don't have that information."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # Rephrase prompt for history-aware retrieval
        rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")

        # ============================================
        # PRE-RETRIEVAL CHECK: Test relevance
        # ============================================
        print("🔎 Retrieving relevant documents...")
        test_docs = vector_store.similarity_search(query, k=k)

        if not test_docs:
            print("⚠️ No documents retrieved")
            return {
                "query": query,
                "result": "I couldn't find any relevant information in my medical database.",
                "source_documents": []
            }

        # Log retrieved documents
        print(f"📄 Retrieved {len(test_docs)} documents:")
        for i, doc in enumerate(test_docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content[:150].replace('\n', ' ')
            print(f"  {i}. {source}")
            print(f"     Preview: {content_preview}...\n")

        # Check if context is relevant (basic keyword matching)
        context_text = " ".join([doc.page_content.lower() for doc in test_docs])
        query_lower = query.lower()

        # Extract meaningful words from query (> 3 chars)
        query_words = [w for w in query_lower.split() if len(w) > 3]

        # Count how many query words appear in context
        matches = sum(1 for word in query_words if word in context_text)
        relevance_ratio = matches / len(query_words) if query_words else 0

        print(f"🎯 Relevance check: {matches}/{len(query_words)} query terms found in context ({relevance_ratio:.1%})")

        # If very low relevance, warn (but still let LLM try with strict prompt)
        if relevance_ratio < 0.3 and len(query_words) > 2:
            print("⚠️ Warning: Retrieved context may not be relevant to query")

        # ============================================
        # CREATE CHAINS
        # ============================================
        stuff_documents_chain = create_stuff_documents_chain(
            chat,
            retrieval_qa_chat_prompt
        )

        history_aware_retriever = create_history_aware_retriever(
            llm=chat,
            retriever=vector_store.as_retriever(search_kwargs={"k": k}),
            prompt=rephrase_prompt
        )

        qa_chain = create_retrieval_chain(
            retriever=history_aware_retriever,
            combine_docs_chain=stuff_documents_chain,
        )

        # ============================================
        # RUN QUERY
        # ============================================
        print("🤖 Generating response...\n")
        result = qa_chain.invoke(
            input={
                "input": query,
                "chat_history": chat_history
            }
        )

        # ============================================
        # POST-PROCESSING: Verify grounding
        # ============================================
        answer = result["answer"]

        # Check if the answer is a refusal (good - following instructions)
        refusal_phrases = [
            "don't have that information",
            "don't have information about",
            "can only answer questions about",
            "can only help with",
            "not in my",
            "cannot find that information"
        ]

        is_refusal = any(phrase in answer.lower() for phrase in refusal_phrases)

        if is_refusal:
            print("✅ Model correctly refused to answer with irrelevant context")
        else:
            print(f"✅ Generated response ({len(answer)} chars)")

        # Format response
        formatted_result = {
            "query": result["input"],
            "result": answer,
            "source_documents": result["context"],
        }

        print(f"📄 Used {len(result['context'])} source documents\n")

        return formatted_result

    except Exception as e:
        print(f"❌ Error in run_llm: {e}")
        import traceback
        traceback.print_exc()

        # Return error in proper format
        return {
            "query": query,
            "result": f"I encountered an error processing your question: {str(e)}",
            "source_documents": []
        }


# ============================================
# UTILITY FUNCTIONS
# ============================================

def format_sources(documents: List[Document]) -> str:
    """Format source documents into a readable string."""
    if not documents:
        return "No sources available"

    sources = set([doc.metadata.get("source", "Unknown") for doc in documents])
    sources_list = sorted(list(sources))

    formatted = "Sources:\n"
    for i, source in enumerate(sources_list, 1):
        formatted += f"{i}. {source}\n"

    return formatted


def get_relevant_context(query: str, k: int = 4) -> List[Document]:
    """Get relevant documents without running full LLM."""
    vector_store = get_vector_store()
    return vector_store.similarity_search(query, k=k)


def clear_cache():
    """Clear cached components (useful for config changes)."""
    global _vector_store_cache, _embeddings_cache
    _vector_store_cache = None
    _embeddings_cache = None
    print("🧹 Cache cleared")


# ============================================
# MAIN FOR TESTING
# ============================================

if __name__ == "__main__":
    print("Testing RAG system...")

    # Validate vector store
    if not validate_vector_store():
        print("❌ Vector store is empty or invalid!")
        exit(1)

    print("✅ Vector store validated\n")

    # Test query
    test_query = "What is LangChain?"
    print(f"Test query: {test_query}\n")

    result = run_llm(query=test_query)

    print(f"\n{'=' * 60}")
    print("RESULT")
    print(f"{'=' * 60}")
    print(result["result"])
    print(f"\n{format_sources(result['source_documents'])}")

    # Test with follow-up
    print(f"\n{'=' * 60}")
    print("FOLLOW-UP TEST")
    print(f"{'=' * 60}\n")

    chat_history = [
        ("human", test_query),
        ("ai", result["result"])
    ]

    followup = "What are its main components?"
    result2 = run_llm(query=followup, chat_history=chat_history)

    print(result2["result"])