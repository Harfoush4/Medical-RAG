#!/bin/bash

# Medical-RAG Setup Script
# This script automates the setup process for Medical-RAG

set -e  # Exit on error

echo "========================================"
echo "   Medical-RAG Setup Script"
echo "========================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
    print_info "Detected Windows environment"
else
    IS_WINDOWS=false
    print_info "Detected Unix-like environment"
fi

# Step 1: Check Python
echo ""
echo "Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python found: $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PYTHON_VERSION=$(python --version | awk '{print $2}')
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

# Step 2: Check Ollama
echo ""
echo "Step 2: Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n 1)
    print_success "Ollama found: $OLLAMA_VERSION"
else
    print_error "Ollama not found!"
    print_info "Please install Ollama from: https://ollama.ai/"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Create virtual environment
echo ""
echo "Step 3: Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Step 4: Activate virtual environment and install dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
if [ "$IS_WINDOWS" = true ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
print_success "Dependencies installed"

# Step 5: Pull Ollama models
echo ""
echo "Step 5: Pulling required Ollama models..."
print_info "This may take a few minutes depending on your internet connection"

if command -v ollama &> /dev/null; then
    echo ""
    echo "Pulling nomic-embed-text (embedding model)..."
    ollama pull nomic-embed-text
    print_success "Embedding model ready"
    
    echo ""
    echo "Which LLM model would you like to use?"
    echo "1) gemma3:1b (Recommended - Fast, ~1GB)"
    echo "2) llama3.2 (Balanced - ~2GB)"
    echo "3) mistral (Best quality - ~4GB)"
    echo "4) phi3 (Medical focused - ~2GB)"
    echo "5) Skip (I'll do this later)"
    read -p "Enter choice (1-5): " MODEL_CHOICE
    
    case $MODEL_CHOICE in
        1)
            echo "Pulling gemma3:1b..."
            ollama pull gemma3:1b
            print_success "gemma3:1b ready"
            ;;
        2)
            echo "Pulling llama3.2..."
            ollama pull llama3.2
            print_success "llama3.2 ready"
            ;;
        3)
            echo "Pulling mistral..."
            ollama pull mistral
            print_success "mistral ready"
            ;;
        4)
            echo "Pulling phi3..."
            ollama pull phi3
            print_success "phi3 ready"
            ;;
        5)
            print_info "Skipping model download. Remember to pull a model later!"
            ;;
        *)
            print_error "Invalid choice. Skipping model download."
            ;;
    esac
else
    print_info "Skipping Ollama model download (Ollama not installed)"
fi

# Step 6: Create .env file
echo ""
echo "Step 6: Creating environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Created .env file from template"
    print_info "You can edit .env to customize settings"
else
    print_info ".env file already exists"
fi

# Step 7: Ask about ingestion
echo ""
echo "========================================"
echo "   Setup Complete! 🎉"
echo "========================================"
echo ""
print_success "Medical-RAG is ready to use!"
echo ""
echo "Next steps:"
echo ""
echo "1. Build the knowledge base (required - first time only):"
echo "   python ingestion.py"
echo "   (This will take 5-10 minutes)"
echo ""
echo "2. Launch the application:"
if [ "$IS_WINDOWS" = true ]; then
    echo "   venv\\Scripts\\activate"
else
    echo "   source venv/bin/activate"
fi
echo "   streamlit run main2.py"
echo ""
echo "Would you like to run the ingestion now?"
read -p "Run ingestion? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    print_info "Starting ingestion process..."
    print_info "This will crawl MedlinePlus and build the vector database"
    print_info "Expected time: 5-10 minutes"
    echo ""
    $PYTHON_CMD ingestion.py
    
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Knowledge base built successfully!"
        echo ""
        echo "You can now launch the app:"
        echo "   streamlit run main2.py"
    else
        print_error "Ingestion failed. Please check the error messages above."
        exit 1
    fi
else
    echo ""
    print_info "Skipping ingestion. Run 'python ingestion.py' when ready."
fi

echo ""
echo "========================================"
echo "   Useful Commands"
echo "========================================"
echo ""
echo "Start the app:"
echo "  streamlit run main2.py"
echo ""
echo "Rebuild knowledge base:"
echo "  python ingestion.py"
echo ""
echo "Check Ollama models:"
echo "  ollama list"
echo ""
echo "Pull more models:"
echo "  ollama pull model-name"
echo ""
echo "========================================"
echo ""
print_success "Happy querying! 🏥"
echo ""
