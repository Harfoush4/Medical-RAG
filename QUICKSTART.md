# Medical-RAG Quick Start Guide

Get up and running with Medical-RAG in under 10 minutes!

## ⚡ Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] At least 8GB of RAM
- [ ] 5GB of free disk space
- [ ] Internet connection (for initial setup)
- [ ] Terminal/Command Prompt access

## 🚀 5-Step Setup

### Step 1: Install Ollama (2 minutes)

**Windows/Mac/Linux:**
Visit [ollama.ai](https://ollama.ai/) and download the installer for your OS.

**Verify installation:**
```bash
ollama --version
```

### Step 2: Pull Required Models (3-5 minutes)

```bash
# Essential embedding model (required)
ollama pull nomic-embed-text

# Language model (choose one - recommended: gemma3:1b for speed)
ollama pull gemma3:1b
```

**Alternative models** (optional):
```bash
ollama pull llama3.2    # Better quality, slower
ollama pull mistral     # Best quality, slowest  
ollama pull phi3        # Good for medical domain
```

### Step 3: Clone and Install (1 minute)

```bash
# Clone repository
git clone https://github.com/Harfoush4/Medical-RAG.git
cd Medical-RAG

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Build Knowledge Base (5-10 minutes)

```bash
# This will crawl MedlinePlus and create the vector database
python ingestion.py
```

**What's happening:**
- Crawling ~500 pages from MedlinePlus
- Splitting documents into chunks
- Creating embeddings
- Storing in ChromaDB

**Expected output:**
```
RAG INGESTION PIPELINE
[STEP 1] Loading documents
  Recursively crawling: https://medlineplus.gov/...
  ✅ Crawled 487 pages
[STEP 2] Splitting documents
  Created 3,421 chunks
[STEP 3] Saving to vector store
  ✅ Saved successfully to chroma_db/
INGESTION COMPLETE
```

### Step 5: Launch the App (30 seconds)

```bash
streamlit run main2.py
```

The app will automatically open in your browser at `http://localhost:8501`

## 🎯 First Queries to Try

Once the app is running, try these example questions:

1. **Basic drug info:**
   - "What is aspirin used for?"
   - "What is metformin?"

2. **Side effects:**
   - "What are the side effects of ibuprofen?"
   - "What are aspirin side effects?"

3. **Usage instructions:**
   - "How should I take amoxicillin?"
   - "When should I take statins?"

4. **Interactions:**
   - "What drugs interact with warfarin?"
   - "Can I take aspirin with ibuprofen?"

5. **Follow-up questions:**
   ```
   You: "What is lisinopril?"
   Bot: "Lisinopril is an ACE inhibitor used to treat high blood pressure..."
   You: "What are its side effects?"  ← Bot understands context!
   ```

## ⚙️ Basic Configuration

### Change the Model

In the app sidebar:
1. Click on "LLM Model" dropdown
2. Select your preferred model
3. New queries will use the new model

### Adjust Response Style

- **Temperature**: Lower (0.1-0.3) = More focused, Higher (0.7-1.0) = More creative
- **Documents to Retrieve**: More documents = More context but slower

## 🐛 Troubleshooting

### Problem: "No module named 'X'"
**Solution:** Install missing package
```bash
pip install X
```

### Problem: "Ollama connection error"
**Solution:** Make sure Ollama is running
```bash
# Check if Ollama is running
ollama list

# Start Ollama service (varies by OS)
# Usually it auto-starts, but you can try:
ollama serve
```

### Problem: "No documents found in vector store"
**Solution:** Run ingestion again
```bash
python ingestion.py
```

### Problem: "Port 8501 already in use"
**Solution:** Stop other Streamlit apps or change port
```bash
streamlit run main2.py --server.port 8502
```

### Problem: Slow responses
**Solutions:**
1. Switch to a smaller model (gemma3:1b)
2. Reduce "Documents to Retrieve" in sidebar
3. Lower temperature slightly

### Problem: "Out of memory"
**Solutions:**
1. Use gemma3:1b model (smallest)
2. Reduce k documents in sidebar
3. Close other applications
4. Reduce RECURSIVE_MAX_PAGES in ingestion.py

## 📊 System Requirements by Model

| Model | RAM | Speed | Quality |
|-------|-----|-------|---------|
| gemma3:1b | 2-4GB | ⚡⚡⚡ Fast | Good |
| llama3.2 | 4-6GB | ⚡⚡ Medium | Better |
| mistral | 6-8GB | ⚡ Slow | Best |
| phi3 | 4-6GB | ⚡⚡ Medium | Better |

**Recommendation**: Start with `gemma3:1b` for best performance.

## 🔄 Updating the Knowledge Base

To update with fresh MedlinePlus data:

```bash
# Delete old database
rm -rf chroma_db/  # Linux/Mac
# OR
rmdir /s chroma_db  # Windows

# Re-run ingestion
python ingestion.py
```

## 💡 Tips for Best Results

1. **Be specific**: "What are the side effects of aspirin?" vs "Tell me about aspirin"
2. **Use follow-ups**: The bot remembers conversation context
3. **Check sources**: Click "View Sources" to see where answers come from
4. **Verify information**: This is not medical advice - always consult a doctor

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **Customize data sources** - Edit `ingestion.py` to add more medical websites
2. **Tune parameters** - Adjust chunk size, overlap, retrieval count
3. **Try different models** - Experiment to find the best balance
4. **Add more data** - Crawl additional medical resources
5. **Read the full README** - Learn about advanced features

## 📚 Quick Reference Commands

```bash
# Start app
streamlit run main2.py

# Re-build database
python ingestion.py

# Update dependencies
pip install -r requirements.txt --upgrade

# Check Ollama models
ollama list

# Pull new model
ollama pull model-name
```

## 🆘 Getting Help

- **GitHub Issues**: [Report bugs or ask questions](https://github.com/Harfoush4/Medical-RAG/issues)
- **Documentation**: Read the full [README.md](README.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## ⚠️ Important Reminder

**This system is for informational purposes only and is NOT a substitute for professional medical advice.**

Always consult with a qualified healthcare provider for medical decisions.

---

**That's it! You're ready to use Medical-RAG. Happy querying! 🏥✨**
