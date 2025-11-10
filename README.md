# Medical-RAG 🏥

A Retrieval-Augmented Generation (RAG) system for accurate medical question-answering using MedlinePlus drug information. Built with LangChain, Ollama, and ChromaDB to provide reliable, source-backed medical information while preventing AI hallucinations.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-latest-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

- **🔒 Privacy-First**: Runs completely locally using Ollama - no data sent to external APIs
- **📚 Medical Knowledge Base**: Crawls and indexes MedlinePlus drug information
- **🎯 Context-Grounded Responses**: Strict prompt engineering prevents hallucinations
- **💬 Conversational Interface**: Maintains chat history for follow-up questions
- **📝 Source Citation**: Every answer includes references to source documents
- **⚙️ Configurable**: Multiple LLM models, adjustable retrieval parameters
- **🖥️ User-Friendly UI**: Clean Streamlit interface with real-time chat

## 🏗️ Architecture

```
┌─────────────────┐
│  MedlinePlus    │
│  Website        │
└────────┬────────┘
         │https://github.com/Harfoush4/Medical-RAG
         ▼
┌─────────────────┐
│  Web Crawler    │
│  (Recursive)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Text Splitter  │
│  (Chunks)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Embeddings     │◄─────┤  Ollama      │
│  (nomic-embed)  │      │  (Local LLM) │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  ChromaDB       │
│  Vector Store   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Chain      │
│  (LangChain)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit UI   │
│  (Chat Interface)│
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Harfoush4/Medical-RAG.git
cd Medical-RAG
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Pull required Ollama models**
```bash
# Embedding model
ollama pull nomic-embed-text

# LLM models (choose at least one)
ollama pull gemma3:1b      # Recommended - fast and lightweight
ollama pull llama3.2       # Alternative
ollama pull mistral        # Alternative
ollama pull phi3           # Alternative
```

4. **Set up environment variables**
```bash
# Create .env file (optional)
cp .env.example .env
# Edit .env with your configuration
```

### Usage

#### Step 1: Ingest Medical Data

Run the ingestion pipeline to crawl MedlinePlus and build the vector database:

```bash
python ingestion.py
```

**Configuration options in `ingestion.py`:**
```python
DATA_SOURCE = "RECURSIVE_CRAWL"
RECURSIVE_START_URL = "https://medlineplus.gov/druginformation.html"
RECURSIVE_MAX_DEPTH = 3        # Link depth
RECURSIVE_MAX_PAGES = 500      # Max pages to crawl
CHUNK_SIZE = 1000              # Characters per chunk
CHUNK_OVERLAP = 30             # Overlap between chunks
VECTOR_STORE = "CHROMA"
CHROMA_DIRECTORY = "chroma_db_doctora_async"
```

This will:
- Crawl MedlinePlus drug information pages
- Split documents into manageable chunks
- Generate embeddings using nomic-embed-text
- Store in ChromaDB (~5-10 minutes depending on settings)

#### Step 2: Launch the Chat Interface

Start the Streamlit application:

```bash
streamlit run main2.py
```

The app will open in your browser at `http://localhost:8501`

#### Step 3: Ask Medical Questions

Example queries:
- "What is aspirin used for?"
- "What are the side effects of metformin?"
- "How should I take ibuprofen?"
- "What are the interactions with warfarin?"

## 📁 Project Structure

```
Medical-RAG/
├── ingestion.py          # Data crawling and vector DB creation
├── core2.py              # RAG logic and query processing
├── main2.py              # Streamlit UI
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
├── chroma_db/            # Vector database (created after ingestion)
└── README.md
```

## 🔧 Configuration

### LLM Models

The system supports multiple Ollama models. Configure in the sidebar:

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| gemma3:1b | ~1GB | ⚡⚡⚡ | ⭐⭐ | Quick responses |
| llama3.2 | ~2GB | ⚡⚡ | ⭐⭐⭐ | Balanced |
| mistral | ~4GB | ⚡ | ⭐⭐⭐ | Complex queries |
| phi3 | ~2GB | ⚡⚡ | ⭐⭐⭐ | Medical domain |

### Retrieval Settings

- **Temperature** (0.0-1.0): Controls response creativity
  - Lower (0.1-0.3): More focused and factual
  - Higher (0.7-1.0): More creative but less reliable
  
- **Documents to Retrieve** (1-10): Number of relevant chunks to use
  - Lower (2-4): Faster, more focused
  - Higher (6-10): More comprehensive context

### Advanced Configuration

Edit `core2.py` for advanced settings:

```python
DEFAULT_CONFIG = {
    "model": "gemma3:1b",
    "temperature": 0.1,
    "k": 4,
    "chroma_path": "chroma_db_doctora_async",
    "embedding_model": "nomic-embed-text",
}
```

## 🎯 Key Features Explained

### 1. Strict Context Grounding

The system uses a specially crafted prompt to ensure answers come only from the retrieved context:

```python
"""
CRITICAL INSTRUCTIONS:
1. Answer questions ONLY using the provided context
2. If the context does not contain the answer, respond with: 
   "I don't have that information in my database."
3. NEVER use your general knowledge or training data
"""
```

This prevents hallucinations and ensures medical accuracy.

### 2. Conversational Memory

Maintains chat history for context-aware follow-up questions:

```python
User: "What is aspirin?"
Bot: "Aspirin is a pain reliever..."

User: "What are its side effects?"  # Understands "its" refers to aspirin
Bot: "Aspirin's side effects include..."
```

### 3. Source Transparency

Every response includes citations to source documents from MedlinePlus, allowing verification.

### 4. Relevance Checking

Pre-filters retrieved documents to ensure they're relevant to the query before generating a response.

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Ollama (Gemma, Llama, Mistral, Phi) | Local language models |
| **Embeddings** | nomic-embed-text | Document vectorization |
| **Vector DB** | ChromaDB | Semantic search |
| **Framework** | LangChain | RAG orchestration |
| **UI** | Streamlit | Web interface |
| **Crawling** | RecursiveUrlLoader | Web scraping |
| **Parsing** | BeautifulSoup | HTML parsing |

## 📊 Performance

- **Ingestion Time**: 5-10 minutes for ~500 pages
- **Query Response**: 2-5 seconds (depends on model and hardware)
- **Memory Usage**: 2-8GB (depends on model)
- **Disk Space**: ~500MB for vector database

## 🔒 Privacy & Security

- ✅ **100% Local**: All processing happens on your machine
- ✅ **No External API Calls**: No data sent to OpenAI, Google, etc.
- ✅ **HIPAA-Friendly**: Suitable for handling sensitive medical queries
- ✅ **Offline Capable**: Works without internet (after initial model download)

## 🚧 Limitations

- **Scope**: Currently limited to MedlinePlus drug information
- **Medical Advice**: Not a substitute for professional medical advice
- **Accuracy**: Depends on source data quality and LLM capabilities
- **Real-Time Updates**: Database needs manual refresh for new information

## 🤝 Contributing

Contributions are welcome! Here are some ways to contribute:

1. **Add new data sources** (medical textbooks, clinical guidelines)
2. **Improve prompts** for better answer quality
3. **Add evaluation metrics** for response accuracy
4. **Enhance UI** with better visualizations
5. **Optimize performance** (faster retrieval, smaller models)

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/Medical-RAG.git
cd Medical-RAG

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests (if available)
pytest tests/
```

## 📝 TODO

- [ ] Add support for more medical databases (PubMed, WHO)
- [ ] Implement evaluation metrics (RAGAS, LangChain evaluators)
- [ ] Add multi-language support
- [ ] Create Docker container for easier deployment
- [ ] Add user authentication and query history
- [ ] Implement feedback mechanism for answer quality
- [ ] Add medical entity extraction and highlighting
- [ ] Create API endpoint for external integrations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This system is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.**

Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read from this system.

## 🙏 Acknowledgments

- **MedlinePlus** for providing comprehensive drug information
- **LangChain** for the RAG framework
- **Ollama** for local LLM capabilities
- **ChromaDB** for efficient vector storage
- The open-source community for inspiration and tools

## 📧 Contact

For questions, issues, or suggestions:

- **GitHub Issues**: [Create an issue](https://github.com/Harfoush4/Medical-RAG/issues)
- **Pull Requests**: [Submit a PR](https://github.com/Harfoush4/Medical-RAG/pulls)

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐!

---

**Built with ❤️ for better medical information access**
