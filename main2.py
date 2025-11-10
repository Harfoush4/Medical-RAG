from typing import Set, List, Dict
import streamlit as st
from Backend.core2 import run_llm, get_config
import json
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin-top: 0.5rem;
    }
    .stats-box {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "user_prompt_history" not in st.session_state:
    st.session_state["user_prompt_history"] = []

if "chat_answer_history" not in st.session_state:
    st.session_state["chat_answer_history"] = []

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "source_documents" not in st.session_state:
    st.session_state["source_documents"] = []

# ============================================
# SIDEBAR - CONFIGURATION & CONTROLS
# ============================================
with st.sidebar:
    st.title("⚙️ Settings")

    # Model selection
    st.subheader("Model Configuration")
    model_option = st.selectbox(
        "LLM Model",
        ["gemma3:1b", "llama3.2", "mistral", "phi3"],
        help="Select the language model to use"
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher = more creative, Lower = more focused"
    )

    # Retrieval settings
    st.subheader("Retrieval Settings")
    k_documents = st.slider(
        "Documents to Retrieve",
        min_value=1,
        max_value=10,
        value=4,
        help="Number of relevant documents to use for answering"
    )

    show_sources = st.checkbox("Show Sources", value=True)
    show_timestamps = st.checkbox("Show Timestamps", value=False)

    st.divider()

    # Statistics
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.metric("Total Messages", len(st.session_state["user_prompt_history"]))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        unique_sources = set()
        for docs in st.session_state.get("source_documents", []):
            unique_sources.update(docs)
        st.metric("Sources Used", len(unique_sources))
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Chat controls
    st.subheader("🎮 Controls")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["user_prompt_history"] = []
        st.session_state["chat_answer_history"] = []
        st.session_state["chat_history"] = []
        st.session_state["source_documents"] = []
        st.rerun()

    if st.button("💾 Export Chat", use_container_width=True):
        if st.session_state["user_prompt_history"]:
            chat_export = []
            for q, a in zip(
                    st.session_state["user_prompt_history"],
                    st.session_state["chat_answer_history"]
            ):
                chat_export.append({"user": q, "assistant": a})

            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(chat_export, indent=2),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.warning("No chat history to export")

    st.divider()

    # Info section
    with st.expander("ℹ️ About"):
        st.markdown("""
        **RAG Assistant** powered by:
        - 🦙 Ollama (Local LLM)
        - 📚 ChromaDB (Vector Store)
        - 🔗 LangChain (Framework)

        Ask questions about your documentation and get accurate, 
        source-backed answers!
        """)

# ============================================
# MAIN CONTENT AREA
# ============================================

# Header
st.title("🤖 RAG Assistant")
st.markdown("Ask questions about your documentation")

# Display chat history
if st.session_state["chat_answer_history"]:
    for idx, (user_query, ai_response) in enumerate(zip(
            st.session_state["user_prompt_history"],
            st.session_state["chat_answer_history"]
    )):
        # User message
        with st.chat_message("user", avatar="👤"):
            if show_timestamps:
                st.caption(f"Message {idx + 1}")
            st.write(user_query)

        # AI message
        with st.chat_message("assistant", avatar="🤖"):
            if show_timestamps:
                st.caption(f"Response {idx + 1}")

            # Split response and sources
            if "\n\nsources:" in ai_response:
                answer_part, sources_part = ai_response.split("\n\nsources:", 1)
                st.write(answer_part)

                if show_sources and sources_part.strip():
                    with st.expander("📚 View Sources", expanded=False):
                        st.markdown(f"**Sources:**\n{sources_part}")
            else:
                st.write(ai_response)

# Chat input area
st.divider()

# Input container
with st.container():
    col1, col2 = st.columns([6, 1])

    with col1:
        prompt = st.chat_input(
            "Ask a question about your documentation...",
            key="chat_input"
        )

    with col2:
        if st.button("🔄", help="Regenerate last response"):
            if st.session_state["user_prompt_history"]:
                # Get last question
                last_question = st.session_state["user_prompt_history"][-1]
                # Remove last Q&A
                st.session_state["user_prompt_history"].pop()
                st.session_state["chat_answer_history"].pop()
                if len(st.session_state["chat_history"]) >= 2:
                    st.session_state["chat_history"].pop()
                    st.session_state["chat_history"].pop()
                # Set as current prompt
                prompt = last_question
                st.rerun()

# ============================================
# QUERY PROCESSING
# ============================================
if prompt:
    # Add user message to UI immediately
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # Show loading state
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔍 Searching documents and generating response..."):
            try:
                # Call the LLM
                generated_response = run_llm(
                    query=prompt,
                    chat_history=st.session_state["chat_history"],
                    model=model_option,
                    temperature=temperature,
                    k=k_documents
                )

                # Extract sources
                sources = set([
                    doc.metadata["source"]
                    for doc in generated_response["source_documents"]
                ])

                # Format response
                answer_text = generated_response["result"]

                if show_sources and sources:
                    sources_list = sorted(list(sources))
                    sources_string = "\n\nsources:\n" + "\n".join(
                        f"{i + 1}. {source}" for i, source in enumerate(sources_list)
                    )
                    formatted_response = answer_text + sources_string
                else:
                    formatted_response = answer_text

                # Display response
                if show_sources and sources:
                    answer_part, sources_part = formatted_response.split("\n\nsources:", 1)
                    st.write(answer_part)

                    with st.expander("📚 View Sources", expanded=True):
                        st.markdown(f"**Sources:**\n{sources_part}")
                else:
                    st.write(formatted_response)

                # Update session state
                st.session_state["user_prompt_history"].append(prompt)
                st.session_state["chat_answer_history"].append(formatted_response)
                st.session_state["chat_history"].append(("human", prompt))
                st.session_state["chat_history"].append(("ai", answer_text))
                st.session_state["source_documents"].append(sources)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

                # Add error to history
                error_msg = f"Error: {str(e)}"
                st.session_state["user_prompt_history"].append(prompt)
                st.session_state["chat_answer_history"].append(error_msg)

# ============================================
# FOOTER
# ============================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("💡 Tip: Ask follow-up questions for context-aware responses")
with col2:
    st.caption("📊 Powered by LangChain & Ollama")
with col3:
    if st.session_state["user_prompt_history"]:
        st.caption(f"📝 {len(st.session_state['user_prompt_history'])} messages")