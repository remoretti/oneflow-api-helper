"""
OneFlow API Feasibility Assistant - Main Streamlit Application
"""
import streamlit as st
import os
from dotenv import load_dotenv
from components.api_docs_processor import APIDocsProcessor
from components.feasibility_analyzer import FeasibilityAnalyzer
from components.response_generator import ResponseGenerator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="OneFlow API Feasibility Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_app():
    """Initialize the application and load necessary components"""
    if 'api_processor' not in st.session_state:
        st.session_state.api_processor = APIDocsProcessor()

    if 'feasibility_analyzer' not in st.session_state:
        st.session_state.feasibility_analyzer = FeasibilityAnalyzer()

    if 'response_generator' not in st.session_state:
        st.session_state.response_generator = ResponseGenerator()

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

def main():
    """Main application function"""
    initialize_app()

    # Sidebar
    with st.sidebar:
        st.title("💼 OneFlow API Feasibility Assistant")
        st.markdown("---")

        st.subheader("About")
        st.write("""
        This tool helps sales teams quickly assess the technical feasibility 
        of customer requirements using OneFlow's API capabilities.
        """)

        st.markdown("---")

        # API Status
        st.subheader("API Status")
        if st.button("Refresh API Documentation"):
            with st.spinner("Refreshing API documentation..."):
                st.session_state.api_processor.refresh_cache()
            st.success("Documentation refreshed!")

        # Show capabilities info
        if hasattr(st.session_state.api_processor, 'knowledge_base'):
            kb = st.session_state.api_processor.knowledge_base
            if kb and 'endpoints' in kb:
                st.metric("Available Endpoints", len(kb['endpoints']))

        # Show business capabilities
        capabilities = st.session_state.feasibility_analyzer.list_capabilities()
        st.metric("Business Capabilities", len(capabilities))

        st.markdown("---")

        # Quick Capability Reference
        st.subheader("Key Capabilities")
        st.write("✅ Contract Creation")
        st.write("✅ File Management")
        st.write("✅ Multi-Party Contracts")
        st.write("✅ Template Management")
        st.write("✅ Webhook Integration")
        st.write("✅ Contact Management")

        st.markdown("---")

        # Export Options
        st.subheader("Export Options")
        if st.session_state.conversation_history:
            if st.button("Export Last Assessment"):
                last_question, last_response = st.session_state.conversation_history[-1]
                # For now, just show the export functionality exists
                st.info("Export functionality available!")

    # Main content area
    st.title("OneFlow API Feasibility Assistant")
    st.markdown("**Ask me about OneFlow's technical capabilities for your sales opportunities!**")

    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        Try asking questions like:
        - "Can we create a contract from a template and add a PDF to it?"
        - "Is it possible to set up multi-party contracts with different signing orders?"
        - "Can we integrate OneFlow with our CRM using webhooks?"
        - "Does OneFlow support automatic data extraction from signed contracts?"
        - "Can we create custom templates through the API?"
        """)

    # Chat interface
    st.markdown("---")

    # Display conversation history
    for i, (question, response) in enumerate(st.session_state.conversation_history):
        with st.container():
            st.markdown(f"**🔍 Question:** {question}")
            st.markdown(response)
            st.markdown("---")

    # Input area
    user_input = st.text_input(
        "What would you like to know about OneFlow's capabilities?",
        placeholder="e.g., Can we create contracts with multiple parties and file attachments?",
        key="user_input"
    )

    # Submit button
    col1, col2 = st.columns([1, 4])
    with col1:
        ask_button = st.button("🔍 Assess Feasibility", type="primary")

    if ask_button and user_input:
        with st.spinner("Analyzing feasibility..."):
            try:
                # Process the user input
                response = process_feasibility_question(user_input)

                # Add to conversation history
                st.session_state.conversation_history.append((user_input, response))

                # Clear input and rerun to show the new conversation
                st.session_state.user_input = ""
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


def process_feasibility_question(question: str) -> str:
    """Process a feasibility question and return a formatted response"""
    try:
        # Analyze feasibility
        assessment = st.session_state.feasibility_analyzer.assess_feasibility(question)

        if not assessment:
            return "I couldn't analyze this question. Please try rephrasing it or check if the system is working properly."

        # Generate sales-friendly response
        response = st.session_state.response_generator.generate_response(assessment, question)

        return response

    except Exception as e:
        return f"Sorry, I encountered an error processing your question: {str(e)}"


if __name__ == "__main__":
    main()