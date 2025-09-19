"""
Enhanced App Integration - Dual Analyzer System
Integrates EnhancedFeasibilityAnalyzer alongside existing FeasibilityAnalyzer
"""

import streamlit as st
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Import your existing components
from components.feasibility_analyzer import FeasibilityAnalyzer
from components.response_generator import ResponseGenerator
from components.api_docs_processor import APIDocsProcessor

# Import the new enhanced system
from enhanced_feasibility_analyzer import EnhancedFeasibilityAnalyzer, EnhancedAssessment

class DualAnalyzerManager:
    """Manages both original and enhanced analyzers"""
    
    def __init__(self):
        """Initialize both analyzer systems"""
        
        # Original system (fallback)
        self.original_analyzer = FeasibilityAnalyzer()
        self.response_generator = ResponseGenerator()
        
        # Enhanced system (primary)
        self.enhanced_analyzer = None
        self.enhanced_available = False
        
        # Initialize enhanced system
        self._initialize_enhanced_system()
    
    def _initialize_enhanced_system(self):
        """Initialize enhanced RAG system with error handling"""
        try:
            with st.spinner("🚀 Initializing Enhanced RAG System..."):
                self.enhanced_analyzer = EnhancedFeasibilityAnalyzer(
                    use_existing_api_processor=True
                )
                self.enhanced_available = True
                st.success("✅ Enhanced RAG System Ready!")
                
        except Exception as e:
            st.warning(f"⚠️ Enhanced system unavailable: {e}")
            st.info("💡 Falling back to original analyzer")
            self.enhanced_available = False
    
    async def assess_feasibility(self, question: str, use_enhanced: bool = True) -> Dict[str, Any]:
        """
        Assess feasibility using either enhanced or original analyzer
        
        Args:
            question: User's question
            use_enhanced: Whether to try enhanced analyzer first
            
        Returns:
            Standardized assessment result
        """
        
        start_time = time.time()
        
        # Try enhanced analyzer first if available and requested
        if use_enhanced and self.enhanced_available:
            try:
                enhanced_result = await self.enhanced_analyzer.assess_feasibility_enhanced(question)
                processing_time = time.time() - start_time
                
                return self._format_enhanced_result(enhanced_result, processing_time)
                
            except Exception as e:
                st.warning(f"Enhanced analysis failed: {e}")
                st.info("🔄 Falling back to original analyzer...")
        
        # Fallback to original analyzer
        try:
            original_result = self.original_analyzer.assess_feasibility(question)
            processing_time = time.time() - start_time
            
            return self._format_original_result(original_result, processing_time)
            
        except Exception as e:
            return self._create_error_result(str(e), time.time() - start_time)
    
    def _format_enhanced_result(self, assessment: EnhancedAssessment, processing_time: float) -> Dict[str, Any]:
        """Format enhanced assessment result for UI"""
        
        # Determine status icon
        status_icons = {
            "YES": "✅",
            "NO": "❌", 
            "CONDITIONAL": "⚠️",
            "NEEDS_ANALYSIS": "🔍"
        }
        
        status_icon = status_icons.get(assessment.feasibility, "❓")
        
        return {
            "type": "enhanced",
            "status": f"{status_icon} {assessment.feasibility}",
            "confidence": f"🎯 {assessment.confidence:.0%}",
            "explanation": assessment.explanation,
            "api_requirements": assessment.api_requirements,
            "integration_complexity": assessment.integration_complexity,
            "business_context": assessment.business_context,
            "caveats": assessment.caveats,
            "related_endpoints": assessment.related_endpoints,
            "integration_patterns": assessment.integration_patterns,
            "implementation_steps": assessment.implementation_steps,
            "sources": assessment.sources,
            "processing_time": processing_time,
            "raw_assessment": assessment
        }
    
    def _format_original_result(self, assessment: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Format original assessment result for UI"""
        
        # Convert original format to enhanced format for consistent UI
        feasibility = assessment.get('feasibility', 'Conditional')
        confidence = assessment.get('confidence', 'Medium')
        
        # Map confidence to percentage
        confidence_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
        confidence_score = confidence_map.get(confidence, 0.5)
        
        status_icons = {
            "Yes": "✅",
            "No": "❌",
            "Conditional": "⚠️"
        }
        
        status_icon = status_icons.get(feasibility, "❓")
        
        return {
            "type": "original",
            "status": f"{status_icon} {feasibility}",
            "confidence": f"🎯 {confidence_score:.0%}",
            "explanation": assessment.get('quick_answer', 'Assessment completed'),
            "api_requirements": ["Original analyzer - API requirements not detailed"],
            "integration_complexity": confidence,  # Use confidence as complexity proxy
            "business_context": assessment.get('business_impact', 'Standard implementation'),
            "caveats": assessment.get('important_caveats', []),
            "related_endpoints": [],
            "integration_patterns": assessment.get('related_features', []),
            "implementation_steps": ["Contact technical team for detailed implementation"],
            "sources": [],
            "processing_time": processing_time,
            "raw_assessment": assessment
        }
    
    def _create_error_result(self, error: str, processing_time: float) -> Dict[str, Any]:
        """Create error result when both analyzers fail"""
        
        return {
            "type": "error",
            "status": "❌ ERROR",
            "confidence": "❓ Unknown",
            "explanation": f"Assessment failed: {error}",
            "api_requirements": ["Manual review required"],
            "integration_complexity": "UNKNOWN",
            "business_context": "Unable to analyze due to system error",
            "caveats": ["System error occurred", "Manual technical review needed"],
            "related_endpoints": [],
            "integration_patterns": [],
            "implementation_steps": ["Contact technical support"],
            "sources": [],
            "processing_time": processing_time,
            "raw_assessment": {}
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both analyzer systems"""
        
        status = {
            "original_available": True,  # Always available
            "enhanced_available": self.enhanced_available,
            "recommended_mode": "enhanced" if self.enhanced_available else "original"
        }
        
        if self.enhanced_available:
            try:
                # Get collection statistics
                collection_stats = self.enhanced_analyzer.get_collection_stats()
                status["collection_stats"] = collection_stats
                status["total_documents"] = sum(collection_stats.values())
            except Exception as e:
                status["collection_stats"] = {}
                status["error"] = str(e)
        
        return status

# Enhanced UI Components for the new system
class EnhancedUI:
    """Enhanced UI components for dual analyzer system"""
    
    @staticmethod
    def render_system_status(status: Dict[str, Any]):
        """Render system status in sidebar"""
        
        st.sidebar.markdown("## 🔧 System Status")
        
        # Original system status
        st.sidebar.success("✅ Original Analyzer: Active")
        
        # Enhanced system status
        if status["enhanced_available"]:
            st.sidebar.success("✅ Enhanced RAG: Active")
            
            # Collection statistics
            if "collection_stats" in status:
                st.sidebar.markdown("### 📊 Knowledge Base")
                total_docs = status.get("total_documents", 0)
                st.sidebar.metric("Total Documents", total_docs)
                
                # Show collection breakdown
                for collection, count in status["collection_stats"].items():
                    collection_name = collection.replace("_", " ").title()
                    st.sidebar.metric(collection_name, count)
        else:
            st.sidebar.warning("⚠️ Enhanced RAG: Unavailable")
            st.sidebar.info("Using original analyzer")
        
        # Mode selection
        st.sidebar.markdown("### ⚙️ Analysis Mode")
        recommended = status["recommended_mode"]
        return st.sidebar.radio(
            "Analyzer Mode",
            ["enhanced", "original"],
            index=0 if recommended == "enhanced" else 1,
            help="Enhanced mode uses advanced RAG with multiple knowledge sources"
        )
    
    @staticmethod
    def render_enhanced_assessment(result: Dict[str, Any]):
        """Render enhanced assessment result"""
        
        # Header with status and confidence
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(result["status"])
        with col2:
            st.metric("Confidence", result["confidence"])
            st.caption(f"⚡ {result['processing_time']:.2f}s")
        
        # Main explanation
        st.markdown("### 💡 Assessment Summary")
        st.info(result["explanation"])
        
        # Enhanced content in tabs (only for enhanced results)
        if result["type"] == "enhanced":
            tab1, tab2, tab3, tab4 = st.tabs([
                "🔧 Technical Requirements",
                "💼 Business Context", 
                "⚠️ Caveats & Limitations",
                "📋 Implementation"
            ])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    if result["api_requirements"]:
                        st.markdown("**API Requirements**")
                        for req in result["api_requirements"]:
                            st.write(f"• {req}")
                    
                    if result["related_endpoints"]:
                        st.markdown("**Related Endpoints**")
                        for endpoint in result["related_endpoints"]:
                            st.code(endpoint, language="http")
                
                with col2:
                    st.markdown("**Integration Complexity**")
                    complexity = result["integration_complexity"]
                    complexity_colors = {
                        "LOW": "🟢",
                        "MEDIUM": "🟡", 
                        "HIGH": "🔴"
                    }
                    
                    for level in ["LOW", "MEDIUM", "HIGH"]:
                        if level in complexity:
                            st.write(f"{complexity_colors[level]} {complexity}")
                            break
                    else:
                        st.write(f"🔵 {complexity}")
            
            with tab2:
                st.markdown("**Business Context**")
                st.write(result["business_context"])
                
                if result["integration_patterns"]:
                    st.markdown("**Applicable Integration Patterns**")
                    for pattern in result["integration_patterns"]:
                        st.write(f"🔗 {pattern}")
            
            with tab3:
                if result["caveats"]:
                    for caveat in result["caveats"]:
                        st.warning(f"⚠️ {caveat}")
                else:
                    st.success("✅ No significant limitations identified")
            
            with tab4:
                if result["implementation_steps"]:
                    st.markdown("**Implementation Steps**")
                    for i, step in enumerate(result["implementation_steps"], 1):
                        st.write(f"{i}. {step}")
                else:
                    st.info("Implementation steps not available")
        
        else:
            # Simplified view for original analyzer results
            col1, col2 = st.columns(2)
            
            with col1:
                if result["caveats"]:
                    st.markdown("**Important Considerations**")
                    for caveat in result["caveats"]:
                        st.warning(f"⚠️ {caveat}")
            
            with col2:
                st.markdown("**Business Impact**") 
                st.write(result["business_context"])
    
    @staticmethod
    def render_knowledge_management():
        """Render knowledge base management interface"""
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("## 📚 Knowledge Base")
        
        # Add documents section
        with st.sidebar.expander("➕ Add Documents"):
            st.write("Upload integration documents to enhance the knowledge base")
            
            uploaded_files = st.file_uploader(
                "Integration Documents",
                type=['md', 'txt', 'pdf'],
                accept_multiple_files=True,
                help="Upload markdown, text, or PDF files"
            )
            
            if uploaded_files and st.button("Process Documents"):
                st.info("Document processing not yet implemented")
                # TODO: Implement document processing
        
        # Refresh knowledge base
        if st.sidebar.button("🔄 Refresh Knowledge Base"):
            st.rerun()

# Main enhanced application
def main_enhanced():
    """Enhanced main application with dual analyzer system"""
    
    # Page configuration
    st.set_page_config(
        page_title="🤖 Enhanced OneFlow Sales Assistant",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'analyzer_manager' not in st.session_state:
        st.session_state.analyzer_manager = DualAnalyzerManager()
    
    # Header
    st.title("🤖 Enhanced OneFlow Sales Assistant")
    st.caption("Advanced RAG-powered technical feasibility assessment with hybrid retrieval")
    
    # System status and controls
    analyzer_manager = st.session_state.analyzer_manager
    system_status = analyzer_manager.get_system_status()
    
    # Sidebar
    with st.sidebar:
        st.title("💼 OneFlow Assistant")
        st.markdown("---")
        
        # System status
        analysis_mode = EnhancedUI.render_system_status(system_status)
        
        # Knowledge management
        EnhancedUI.render_knowledge_management()
        
        st.markdown("---")
        
        # Session stats
        st.markdown("## 📊 Session Stats")
        if 'assessment_count' not in st.session_state:
            st.session_state.assessment_count = 0
        
        st.metric("Assessments Today", st.session_state.assessment_count)
        
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Main chat interface
    st.markdown("---")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **API Integration Questions:**
        - "Can we create a contract from a template and add a PDF to it?"
        - "What endpoints do we need for multi-party contracts?"
        
        **Business Integration Questions:**  
        - "How do we integrate OneFlow with Salesforce?"
        - "What's the complexity of a CRM integration?"
        
        **Implementation Questions:**
        - "What are the steps to build a web form integration?"
        - "How do we handle webhook notifications?"
        """)
    
    # Chat input
    user_input = st.text_input(
        "Ask about OneFlow integration capabilities...",
        placeholder="e.g., How complex is integrating OneFlow with our CRM system?",
        key="enhanced_chat_input"
    )
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        assess_button = st.button("🔍 Assess Feasibility", type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear Conversation")
    
    # Process user input
    if assess_button and user_input:
        st.session_state.assessment_count += 1
        
        # Add to conversation history
        conversation_entry = {
            'question': user_input,
            'timestamp': datetime.now(),
            'status': 'processing'
        }
        st.session_state.conversation_history.append(conversation_entry)
        
        # Show processing
        with st.spinner("🤖 Analyzing with advanced system..."):
            # Use async assessment
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    analyzer_manager.assess_feasibility(
                        user_input, 
                        use_enhanced=(analysis_mode == "enhanced")
                    )
                )
            finally:
                loop.close()
        
        # Update conversation history
        st.session_state.conversation_history[-1].update({
            'result': result,
            'status': 'complete',
            'analysis_mode': analysis_mode
        })
        
        st.rerun()
    
    # Handle clear button
    if clear_button:
        st.session_state.conversation_history = []
        st.rerun()
    
    # Display conversation history
    st.markdown("## 💬 Assessment History")
    
    for i, convo in enumerate(reversed(st.session_state.conversation_history)):
        with st.expander(
            f"🔍 {convo['question'][:100]}..." if len(convo['question']) > 100 else f"🔍 {convo['question']}", 
            expanded=(i == 0)
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📅 {convo['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                mode_badge = "🚀 Enhanced" if convo.get('analysis_mode') == 'enhanced' else "⚡ Original"
                st.caption(mode_badge)
            
            if convo['status'] == 'complete':
                EnhancedUI.render_enhanced_assessment(convo['result'])
            else:
                st.info("⏳ Processing...")

if __name__ == "__main__":
    main_enhanced()