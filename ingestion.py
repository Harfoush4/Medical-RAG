import asyncio
import os
import ssl
from typing import Any,Dict,List
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import SitemapLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_tavily import TavilyCrawl, TavilyExtract , TavilyMap
import certifi
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from langchain_community.document_loaders.rss import RSSFeedLoader

# Text splitters
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
)

# Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Vector stores
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
from langchain_pinecone import PineconeVectorStore

# Tavily and Documents
from langchain_tavily import TavilyCrawl
from langchain_core.documents import Document
from logger import (Colors,log_error,log_header,log_info,log_success,log_warning)

load_dotenv()

# Data source
DATA_SOURCE = "RECURSIVE_CRAWL"  # ← NEW OPTION

# Recursive crawl settings
RECURSIVE_START_URL = "https://medlineplus.gov/druginformation.html"
RECURSIVE_MAX_DEPTH = 3  # How deep to follow links (3 is good for docs)
RECURSIVE_MAX_PAGES = 500  # Safety limit

SITEMAP_URL = "https://python.langchain.com/sitemap.xml"

SPLITTER_TYPE = "CHARACTER"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 30
VECTOR_STORE = "CHROMA"
CHROMA_DIRECTORY = "chroma_db_doctora_async"

embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)


def crawl_website_recursive(start_url, max_depth=3, max_pages=200):
    """
    Recursively crawl a website starting from one URL.
    Follows all internal links automatically.

    Args:
        start_url: Starting URL (e.g., "https://python.langchain.com/")
        max_depth: How many link levels deep to go
        max_pages: Maximum pages to scrape (prevents infinite crawling)
    """
    print(f"\nRecursively crawling: {start_url}")
    print(f"  Max depth: {max_depth}, Max pages: {max_pages}")

    try:
        # Create recursive loader
        loader = RecursiveUrlLoader(
            url=start_url,
            max_depth=max_depth,
            extractor=lambda x: BeautifulSoup(x, "lxml").text,
            prevent_outside=True,  # Only follow links within same domain
            use_async=False,  # Faster crawling when it is True
            timeout=30,
            check_response_status=False,  # ← Ignore errors
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        # Load documents
        print("  Starting crawl (this may take a few minutes)...")
        documents = loader.load()

        # Limit if too many
        if len(documents) > max_pages:
            print(f"  ⚠️ Got {len(documents)} pages, limiting to {max_pages}")
            documents = documents[:max_pages]

        print(f"  ✅ Crawled {len(documents)} pages")

        # Show some stats
        if documents:
            total_chars = sum(len(doc.page_content) for doc in documents)
            print(f"  Total content: {total_chars:,} characters")
            print(f"  Unique sources: {len(set(doc.metadata.get('source', '') for doc in documents))}")

        return documents

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def crawl_sitemap(sitemap_url, filter_urls=None, max_pages=None):
    """
    Crawl sitemap with improved error handling and options.
    """
    import requests
    from bs4 import BeautifulSoup

    print(f"\nCrawling sitemap: {sitemap_url}")

    try:
        # Method 1: Try with SitemapLoader
        try:
            from langchain_community.document_loaders import SitemapLoader

            loader = SitemapLoader(
                web_path=sitemap_url,
                filter_urls=filter_urls,
                parsing_function=lambda x: BeautifulSoup(x, 'html.parser').get_text(),
            )
            documents = loader.load()

            if len(documents) > 0:
                print(f"  ✅ Crawled {len(documents)} pages from sitemap")
                return documents
        except Exception as e:
            print(f"  SitemapLoader failed: {e}")

        # Method 2: Manual parsing
        print(f"  Trying manual sitemap parsing...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(sitemap_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]

        print(f"  Found {len(urls)} URLs in sitemap")

        # Apply filters
        if filter_urls:
            urls = [url for url in urls if any(f in url for f in filter_urls)]
            print(f"  Filtered to {len(urls)} URLs")

        # Limit if needed
        if max_pages and len(urls) > max_pages:
            print(f"  Limiting to {max_pages} pages")
            urls = urls[:max_pages]

        if not urls:
            print(f"  ⚠️ No URLs found after filtering")
            return []

        # Load with WebBaseLoader
        from langchain_community.document_loaders import WebBaseLoader

        print(f"  Loading {len(urls)} pages...")
        loader = WebBaseLoader(urls)
        documents = loader.load()

        print(f"  ✅ Crawled {len(documents)} pages")
        return documents

    except Exception as e:
        print(f"  ❌ Error crawling sitemap: {e}")
        import traceback
        traceback.print_exc()
        return []

def split_documents(documents, splitter_type="CHARACTER", chunk_size=1000, chunk_overlap=30):
    """
    Split documents into chunks using different splitter types.
    Types: CHARACTER, RECURSIVE, MARKDOWN
    """
    print(f"Splitting documents with {splitter_type} splitter")
    print(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")

    if splitter_type == "CHARACTER":
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n"
        )
    elif splitter_type == "RECURSIVE":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    elif splitter_type == "MARKDOWN":
        text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    else:
        print(f"  Unknown splitter type: {splitter_type}, using CHARACTER")
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n"
        )

    docs = text_splitter.split_documents(documents)
    print(f"Created {len(docs)} chunks")
    return docs

def save_to_chroma(docs, embeddings, persist_directory="chroma_db"):
    """Save documents to Chroma vector store."""
    print(f"Saving to ChromaDB: {persist_directory}")
    try:
        vector_store = Chroma.from_documents(
            docs,
            embeddings,
            persist_directory=persist_directory
        )
        print(f"  Saved successfully to {persist_directory}/")
    except Exception as e:
        print(f"  Error saving to Chroma: {e}")


if __name__ == "__main__":
    print("  RAG INGESTION PIPELINE")

    # Step 1: Load documents based on DATA_SOURCE
    print("[STEP 1] Loading documents")

    all_documents = []



    if DATA_SOURCE == "SITEMAP":
        # Free sitemap crawling
        all_documents = crawl_sitemap(SITEMAP_URL)

    elif DATA_SOURCE == "RECURSIVE_CRAWL":  # ← ADD THIS
        all_documents = crawl_website_recursive(
            RECURSIVE_START_URL,
            max_depth=RECURSIVE_MAX_DEPTH,
            max_pages=RECURSIVE_MAX_PAGES
        )





    else:
        raise ValueError(f"Unknown DATA_SOURCE: {DATA_SOURCE}")

    if len(all_documents) == 0:
        print("No documents loaded. Check your configuration.")
        exit(1)

    print(f"Total documents loaded: {len(all_documents)}")

    # Step 2: Split documents into chunks
    print("[STEP 2] Splitting documents")
    docs = split_documents(
        all_documents,
        splitter_type=SPLITTER_TYPE,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Step 3: Save to vector store
    print("[STEP 3] Saving to vector store")


    if VECTOR_STORE == "CHROMA":
        save_to_chroma(docs, embeddings, persist_directory=CHROMA_DIRECTORY)

    else:
        raise ValueError(f"Unknown VECTOR_STORE: {VECTOR_STORE}")

    # Summary
    print("  INGESTION COMPLETE")
    print("Summary")
    print(f"Source: {DATA_SOURCE}")
    print(f"Documents: {len(all_documents)}")
    print(f"Chunks: {len(docs)}")
    print(f"Vector Store: {VECTOR_STORE}")
    print(f"Embedding Model: {embeddings.model if hasattr(embeddings, 'model') else 'Custom'}")
