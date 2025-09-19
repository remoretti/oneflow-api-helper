"""
Enhanced OneFlow RAG System with Hybrid Retrieval
Architecture: Multiple Collections + Cross-Reference + GPT-4o-mini
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import chromadb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
from datetime import datetime
import hashlib
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

class ContentType(Enum):
    API_SPEC = "api_spec"
    INTEGRATION_GUIDE = "integration_guide"
    TUTORIAL = "tutorial"
    GLOSSARY = "glossary"
    USE_CASE = "use_case"

class IntegrationLevel(Enum):
    STANDARD = "standard"
    APPLICATION = "application" 
    PARTNER = "partner"

@dataclass
class SearchResult:
    content: str
    metadata: Dict[str, Any]
    score: float
    source_type: ContentType
    
@dataclass 
class EnhancedAssessment:
    feasibility: str
    confidence: float
    explanation: str
    api_requirements: List[str]
    integration_complexity: str
    business_context: str
    caveats: List[str]
    related_endpoints: List[str]
    integration_patterns: List[str]
    implementation_steps: List[str]
    sources: List[SearchResult]

class EnhancedFeasibilityAnalyzer:
    """
    Advanced RAG-based feasibility analyzer with hybrid retrieval
    Coexists with original FeasibilityAnalyzer as enhanced option
    """
    
    def __init__(self, use_existing_api_processor: bool = True):
        """
        Initialize enhanced analyzer
        
        Args:
            use_existing_api_processor: Whether to use existing APIDocsProcessor
        """
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=2000
        )
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize ChromaDB client  
        self.chroma_client = chromadb.PersistentClient(path="./enhanced_oneflow_db")
        
        # Multiple collections for hybrid approach
        self.collections = {}
        self.vector_stores = {}
        
        # Original API processor integration
        if use_existing_api_processor:
            from components.api_docs_processor import APIDocsProcessor
            self.api_processor = APIDocsProcessor()
        
        # Initialize knowledge base
        self._initialize_hybrid_knowledge_base()
    
    def _initialize_hybrid_knowledge_base(self):
        """Initialize multiple ChromaDB collections for hybrid retrieval"""
        
        print("🚀 Initializing Enhanced OneFlow Knowledge Base...")
        
        # Collection definitions
        collection_configs = {
            "api_specifications": {
                "type": ContentType.API_SPEC,
                "description": "API endpoints, parameters, responses"
            },
            "integration_guides": {
                "type": ContentType.INTEGRATION_GUIDE, 
                "description": "Integration patterns and workflows"
            },
            "tutorials_examples": {
                "type": ContentType.TUTORIAL,
                "description": "Step-by-step guides and examples"
            },
            "glossary_concepts": {
                "type": ContentType.GLOSSARY,
                "description": "Terminology and concept definitions"
            },
            "use_cases_patterns": {
                "type": ContentType.USE_CASE,
                "description": "Business scenarios and patterns"
            }
        }
        
        # Create or get existing collections
        for collection_name, config in collection_configs.items():
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
                print(f"✅ Loaded existing collection: {collection_name}")
            except:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"content_type": config["type"].value}
                )
                print(f"🆕 Created new collection: {collection_name}")
            
            self.collections[collection_name] = collection
            
            # Create Langchain vector store wrapper
            self.vector_stores[collection_name] = Chroma(
                client=self.chroma_client,
                collection_name=collection_name,
                embedding_function=self.embeddings
            )
        
        # Load documents if collections are empty
        self._populate_collections_if_needed()
    
    def _populate_collections_if_needed(self):
        """Populate collections with documents if they're empty"""
        
        for collection_name, collection in self.collections.items():
            if collection.count() == 0:
                print(f"📄 Populating {collection_name}...")
                
                if collection_name == "api_specifications":
                    self._populate_api_specifications()
                elif collection_name == "integration_guides":
                    self._populate_integration_guides()
                elif collection_name == "tutorials_examples":
                    self._populate_tutorials()
                elif collection_name == "glossary_concepts": 
                    self._populate_glossary()
                elif collection_name == "use_cases_patterns":
                    self._populate_use_cases()
    
    def _populate_api_specifications(self):
        """Populate API specifications from existing processor"""
        print("📡 Processing API specifications...")
        
        try:
            # Use existing API processor if available
            if hasattr(self, 'api_processor'):
                api_docs = self._process_existing_api_docs()
            else:
                api_docs = self._create_fallback_api_docs()
            
            if api_docs:
                self.vector_stores["api_specifications"].add_documents(api_docs)
                print(f"✅ Added {len(api_docs)} API specification documents")
            
        except Exception as e:
            print(f"⚠️ Error populating API specs: {e}")
            st.warning(f"Could not load API specifications: {e}")
    
    def _process_existing_api_docs(self) -> List[Document]:
        """Process documents from existing API processor"""
        documents = []
        
        try:
            # Get knowledge base from existing processor
            kb = self.api_processor.knowledge_base
            
            if kb and 'endpoints' in kb:
                for endpoint_path, endpoint_data in kb['endpoints'].items():
                    for method, method_data in endpoint_data.items():
                        # Create document for each endpoint + method
                        content = self._format_api_endpoint_content(
                            endpoint_path, method, method_data
                        )
                        
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source_type": ContentType.API_SPEC.value,
                                "endpoint": endpoint_path,
                                "method": method.upper(),
                                "operation_id": method_data.get('operationId', ''),
                                "summary": method_data.get('summary', ''),
                                "complexity": self._assess_endpoint_complexity(method_data)
                            }
                        )
                        documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error processing existing API docs: {e}")
            return []
    
    def _format_api_endpoint_content(self, path: str, method: str, data: Dict) -> str:
        """Format API endpoint data into searchable content"""
        
        content_parts = [
            f"API Endpoint: {method.upper()} {path}",
            f"Summary: {data.get('summary', 'No summary available')}",
            f"Description: {data.get('description', 'No description available')}"
        ]
        
        # Add parameters information
        if 'parameters' in data:
            content_parts.append("Parameters:")
            for param in data['parameters']:
                param_info = f"- {param.get('name', 'unknown')} ({param.get('in', 'unknown')}): {param.get('description', 'No description')}"
                if param.get('required', False):
                    param_info += " [Required]"
                content_parts.append(param_info)
        
        # Add response information
        if 'responses' in data:
            content_parts.append("Responses:")
            for status_code, response_data in data['responses'].items():
                content_parts.append(f"- {status_code}: {response_data.get('description', 'No description')}")
        
        return "\n".join(content_parts)
    
    def _assess_endpoint_complexity(self, method_data: Dict) -> str:
        """Assess complexity of an API endpoint"""
        complexity_score = 0
        
        # Count parameters
        param_count = len(method_data.get('parameters', []))
        complexity_score += min(param_count, 5)  # Cap at 5 points
        
        # Check for required parameters  
        required_params = sum(1 for p in method_data.get('parameters', []) if p.get('required', False))
        complexity_score += required_params
        
        # Check for request body
        if 'requestBody' in method_data:
            complexity_score += 2
        
        # Determine complexity level
        if complexity_score <= 3:
            return "low"
        elif complexity_score <= 7:
            return "medium"
        else:
            return "high"
    
    def _populate_integration_guides(self):
        """Populate integration guides collection"""
        print("🔧 Processing integration guides...")
        
        # TODO: This is where you'll add your first-hand integration docs
        # For now, create placeholder structure
        
        placeholder_guides = [
            {
                "title": "Standard Integration Overview",
                "content": """Standard integrations are account-specific integrations that solve specific use cases. 
                Most data is hardcoded or automatically fetched. Examples include webform contract creation 
                and signup process integration.""",
                "integration_level": IntegrationLevel.STANDARD.value,
                "complexity": "low"
            },
            {
                "title": "Application Integration Patterns", 
                "content": """Application integrations connect OneFlow with external systems like CRM or ATS.
                Data is dynamically collected via UI. Examples include Salesforce and HubSpot integrations.""",
                "integration_level": IntegrationLevel.APPLICATION.value,
                "complexity": "medium"
            },
            {
                "title": "Partner Integration Framework",
                "content": """Partner integrations are generic integrations allowing any account to connect
                with external systems. They rely entirely on dynamic data from systems or users.""",
                "integration_level": IntegrationLevel.PARTNER.value,
                "complexity": "high"
            }
        ]
        
        documents = []
        for guide in placeholder_guides:
            doc = Document(
                page_content=f"{guide['title']}\n\n{guide['content']}",
                metadata={
                    "source_type": ContentType.INTEGRATION_GUIDE.value,
                    "integration_level": guide["integration_level"],
                    "complexity": guide["complexity"],
                    "title": guide["title"]
                }
            )
            documents.append(doc)
        
        if documents:
            self.vector_stores["integration_guides"].add_documents(documents)
            print(f"✅ Added {len(documents)} integration guide documents")
    
    def _populate_tutorials(self):
        """Populate tutorials and examples collection"""
        print("📚 Processing tutorials...")
        
        # Placeholder tutorial content
        tutorials = [
            {
                "title": "Web Form Integration Tutorial",
                "content": """Step-by-step guide for creating contracts via web forms:
                1. Create web form with contract fields
                2. Use contract create endpoint
                3. Publish contract to participants
                4. Handle user authentication for signing""",
                "complexity": "medium",
                "use_case": "web_forms"
            }
        ]
        
        documents = []
        for tutorial in tutorials:
            doc = Document(
                page_content=f"{tutorial['title']}\n\n{tutorial['content']}",
                metadata={
                    "source_type": ContentType.TUTORIAL.value,
                    "complexity": tutorial["complexity"],
                    "use_case": tutorial["use_case"],
                    "title": tutorial["title"]
                }
            )
            documents.append(doc)
        
        if documents:
            self.vector_stores["tutorials_examples"].add_documents(documents)
            print(f"✅ Added {len(documents)} tutorial documents")
    
    def _populate_glossary(self):
        """Populate glossary and concepts collection"""
        print("📖 Processing glossary...")
        
        # Key OneFlow concepts from the documentation
        glossary_terms = [
            {
                "term": "Contract",
                "definition": "A digital agreement created in OneFlow with participants, terms, and signature requirements."
            },
            {
                "term": "Participant", 
                "definition": "A real person in a contract who represents a party. Participants marked as signatories must sign the contract."
            },
            {
                "term": "Party",
                "definition": "A legal entity in a contract (company or individual). All parties are represented by participants."
            },
            {
                "term": "Template",
                "definition": "A predefined contract structure that can be used to create contracts with consistent formatting and fields."
            },
            {
                "term": "Workspace",
                "definition": "A logical separation within an account for organizing contracts, templates, and users with specific permissions."
            }
        ]
        
        documents = []
        for term_data in glossary_terms:
            content = f"Term: {term_data['term']}\nDefinition: {term_data['definition']}"
            doc = Document(
                page_content=content,
                metadata={
                    "source_type": ContentType.GLOSSARY.value,
                    "term": term_data["term"].lower(),
                    "complexity": "low"
                }
            )
            documents.append(doc)
        
        if documents:
            self.vector_stores["glossary_concepts"].add_documents(documents)
            print(f"✅ Added {len(documents)} glossary documents")
    
    def _populate_use_cases(self):
        """Populate use cases and patterns collection"""
        print("💼 Processing use cases...")
        
        use_cases = [
            {
                "title": "CRM Integration Pattern",
                "content": """Common pattern for CRM integration:
                - Sync contact data from CRM to OneFlow
                - Create contracts based on CRM opportunities
                - Update contract status back to CRM
                - Handle multi-party contracts with CRM data""",
                "business_value": "Streamlined sales process",
                "complexity": "medium"
            },
            {
                "title": "E-commerce Checkout Integration",
                "content": """Pattern for e-commerce contract creation:
                - Customer completes purchase
                - System generates contract from order data
                - Automatic contract delivery via email
                - Integration with payment processing""",
                "business_value": "Automated contract fulfillment",
                "complexity": "low"
            }
        ]
        
        documents = []
        for use_case in use_cases:
            doc = Document(
                page_content=f"{use_case['title']}\n\n{use_case['content']}\n\nBusiness Value: {use_case['business_value']}",
                metadata={
                    "source_type": ContentType.USE_CASE.value,
                    "complexity": use_case["complexity"],
                    "business_value": use_case["business_value"],
                    "title": use_case["title"]
                }
            )
            documents.append(doc)
        
        if documents:
            self.vector_stores["use_cases_patterns"].add_documents(documents)
            print(f"✅ Added {len(documents)} use case documents")
    
    def _create_fallback_api_docs(self) -> List[Document]:
        """Create fallback API documentation if processor unavailable"""
        print("⚠️ Creating fallback API documentation")
        
        # Basic API documentation structure
        fallback_docs = [
            {
                "endpoint": "POST /contracts",
                "summary": "Create a new contract",
                "content": """Create a new contract endpoint allows you to programmatically create contracts.
                Requires template ID, participant data, and contract details. Returns contract ID for further operations."""
            },
            {
                "endpoint": "GET /contracts/{id}",
                "summary": "Get contract by ID", 
                "content": """Retrieve contract details by ID. Returns contract status, participants, and metadata.
                Used for checking contract state and progress."""
            }
        ]
        
        documents = []
        for doc_data in fallback_docs:
            doc = Document(
                page_content=f"{doc_data['endpoint']}\n{doc_data['summary']}\n\n{doc_data['content']}",
                metadata={
                    "source_type": ContentType.API_SPEC.value,
                    "endpoint": doc_data["endpoint"],
                    "complexity": "medium"
                }
            )
            documents.append(doc)
        
        return documents
    
    def hybrid_search(self, question: str, k: int = 8) -> List[SearchResult]:
        """
        Hybrid search across multiple collections with smart routing
        
        Args:
            question: User's question
            k: Total number of results to return
            
        Returns:
            List of search results with sources and scores
        """
        
        # Step 1: Query analysis for smart routing
        query_intent = self._analyze_query_intent(question)
        
        # Step 2: Primary targeted search
        primary_results = self._targeted_search(question, query_intent, k//2)
        
        # Step 3: Cross-collection search for context
        context_results = self._cross_collection_search(question, k//2)
        
        # Step 4: Merge, deduplicate, and rank results
        all_results = self._merge_and_rank_results(primary_results, context_results)
        
        return all_results[:k]
    
    def _analyze_query_intent(self, question: str) -> Dict[str, float]:
        """Analyze query to determine which collections are most relevant"""
        
        question_lower = question.lower()
        intent_scores = {}
        
        # API-focused keywords
        api_keywords = ["endpoint", "api", "parameter", "response", "request", "method", "post", "get"]
        api_score = sum(1 for keyword in api_keywords if keyword in question_lower)
        intent_scores["api_specifications"] = api_score
        
        # Integration-focused keywords  
        integration_keywords = ["integrate", "integration", "connect", "sync", "crm", "system", "workflow"]
        integration_score = sum(1 for keyword in integration_keywords if keyword in question_lower)
        intent_scores["integration_guides"] = integration_score
        
        # Tutorial-focused keywords
        tutorial_keywords = ["how to", "tutorial", "example", "step", "guide", "implement"]
        tutorial_score = sum(1 for keyword in tutorial_keywords if keyword in question_lower)
        intent_scores["tutorials_examples"] = tutorial_score
        
        # Use case keywords
        usecase_keywords = ["business", "scenario", "pattern", "value", "benefit", "process"]
        usecase_score = sum(1 for keyword in usecase_keywords if keyword in question_lower)
        intent_scores["use_cases_patterns"] = usecase_score
        
        # Glossary keywords (definitions)
        glossary_keywords = ["what is", "define", "meaning", "term", "concept"]
        glossary_score = sum(1 for keyword in glossary_keywords if keyword in question_lower)
        intent_scores["glossary_concepts"] = glossary_score
        
        return intent_scores
    
    def _targeted_search(self, question: str, intent_scores: Dict[str, float], k: int) -> List[SearchResult]:
        """Perform targeted search based on query intent"""
        
        results = []
        
        # Sort collections by relevance score
        sorted_collections = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Search top 2 most relevant collections
        for collection_name, score in sorted_collections[:2]:
            if score > 0:  # Only search collections with some relevance
                try:
                    collection_results = self.vector_stores[collection_name].similarity_search_with_score(
                        question, k=k//2 if len(sorted_collections) > 1 else k
                    )
                    
                    for doc, similarity_score in collection_results:
                        result = SearchResult(
                            content=doc.page_content,
                            metadata=doc.metadata,
                            score=similarity_score,
                            source_type=ContentType(doc.metadata["source_type"])
                        )
                        results.append(result)
                        
                except Exception as e:
                    print(f"Error searching {collection_name}: {e}")
        
        return results
    
    def _cross_collection_search(self, question: str, k: int) -> List[SearchResult]:
        """Search across all collections for additional context"""
        
        results = []
        per_collection_k = max(1, k // len(self.vector_stores))
        
        for collection_name, vector_store in self.vector_stores.items():
            try:
                collection_results = vector_store.similarity_search_with_score(
                    question, k=per_collection_k
                )
                
                for doc, similarity_score in collection_results:
                    result = SearchResult(
                        content=doc.page_content,
                        metadata=doc.metadata, 
                        score=similarity_score,
                        source_type=ContentType(doc.metadata["source_type"])
                    )
                    results.append(result)
                    
            except Exception as e:
                print(f"Error in cross-collection search for {collection_name}: {e}")
        
        return results
    
    def _merge_and_rank_results(self, primary: List[SearchResult], context: List[SearchResult]) -> List[SearchResult]:
        """Merge and deduplicate results, maintaining diversity"""
        
        # Combine all results
        all_results = primary + context
        
        # Deduplicate based on content similarity (simple approach)
        unique_results = []
        seen_content = set()
        
        for result in sorted(all_results, key=lambda x: x.score):
            # Simple deduplication by content hash
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen_content:
                unique_results.append(result)
                seen_content.add(content_hash)
        
        # Prioritize diversity - ensure we have results from different source types
        final_results = []
        source_type_counts = {}
        
        for result in unique_results:
            source_type = result.source_type
            if source_type_counts.get(source_type, 0) < 3:  # Max 3 per source type
                final_results.append(result)
                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        
        return final_results
    
    async def assess_feasibility_enhanced(self, question: str) -> EnhancedAssessment:
        """Enhanced feasibility assessment with hybrid RAG"""
        
        try:
            # Hybrid search for relevant context
            search_results = self.hybrid_search(question, k=8)
            
            if not search_results:
                return self._create_fallback_enhanced_assessment(question)
            
            # Create enhanced prompt with multiple context types
            enhanced_prompt = self._create_enhanced_prompt(question, search_results)
            
            # GPT-4o-mini assessment
            response = await self.llm.ainvoke(enhanced_prompt.format_messages())
            
            # Parse structured response
            assessment = self._parse_enhanced_response(response.content, search_results)
            
            return assessment
            
        except Exception as e:
            st.error(f"Enhanced assessment failed: {e}")
            return self._create_fallback_enhanced_assessment(question, str(e))
    
    def _create_enhanced_prompt(self, question: str, results: List[SearchResult]) -> ChatPromptTemplate:
        """Create comprehensive prompt with multiple context sources"""
        
        # Organize results by source type
        context_by_type = {}
        for result in results:
            source_type = result.source_type.value
            if source_type not in context_by_type:
                context_by_type[source_type] = []
            context_by_type[source_type].append(result.content)
        
        # Format context sections
        context_sections = []
        for source_type, contents in context_by_type.items():
            section = f"\n--- {source_type.upper().replace('_', ' ')} ---\n"
            section += "\n\n".join(contents)
            context_sections.append(section)
        
        formatted_context = "\n".join(context_sections)
        
        prompt_template = """You are an expert OneFlow integration consultant helping sales teams assess technical feasibility.

CONTEXT FROM ONEFLOW DOCUMENTATION:
{context}

SALES QUESTION: {question}

Provide a comprehensive assessment in JSON format:
{{
    "feasibility": "YES|NO|CONDITIONAL|NEEDS_ANALYSIS",
    "confidence": 0.0-1.0,
    "explanation": "Clear, business-focused explanation",
    "api_requirements": ["Required API endpoints and methods"],
    "integration_complexity": "LOW|MEDIUM|HIGH with detailed reasoning",
    "business_context": "How this fits into business workflows", 
    "caveats": ["Important limitations, dependencies, requirements"],
    "related_endpoints": ["Relevant API endpoints from context"],
    "integration_patterns": ["Applicable integration patterns"],
    "implementation_steps": ["High-level implementation steps"],
    "timeline_estimate": "Realistic development timeline",
    "cost_implications": "Development cost considerations"
}}

GUIDELINES:
- Use business language, avoid technical jargon
- Be specific about API requirements and endpoints
- Consider integration complexity realistically
- Focus on sales impact and business value
- Highlight any deal-breaking limitations
- Reference specific OneFlow capabilities from context
- Provide actionable implementation guidance"""

        return ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", "Context: {context}\n\nQuestion: {question}")
        ]).partial(context=formatted_context, question=question)
    
    def _parse_enhanced_response(self, response_content: str, search_results: List[SearchResult]) -> EnhancedAssessment:
        """Parse enhanced LLM response into structured assessment"""
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return EnhancedAssessment(
                feasibility=data.get("feasibility", "CONDITIONAL"),
                confidence=data.get("confidence", 0.5),
                explanation=data.get("explanation", "Assessment completed"),
                api_requirements=data.get("api_requirements", []),
                integration_complexity=data.get("integration_complexity", "MEDIUM"),
                business_context=data.get("business_context", "Standard integration scenario"),
                caveats=data.get("caveats", []),
                related_endpoints=data.get("related_endpoints", []),
                integration_patterns=data.get("integration_patterns", []),
                implementation_steps=data.get("implementation_steps", []),
                sources=search_results
            )
            
        except Exception as e:
            print(f"Error parsing enhanced response: {e}")
            return self._create_fallback_enhanced_assessment("", str(e))
    
    def _create_fallback_enhanced_assessment(self, question: str, error: str = "") -> EnhancedAssessment:
        """Create fallback assessment when enhanced analysis fails"""
        
        return EnhancedAssessment(
            feasibility="NEEDS_ANALYSIS",
            confidence=0.3,
            explanation=f"Could not complete enhanced analysis. {error}",
            api_requirements=["Manual review required"],
            integration_complexity="UNKNOWN - requires detailed analysis",
            business_context="Unable to determine without proper analysis",
            caveats=["Enhanced analysis system unavailable", "Fallback assessment provided"],
            related_endpoints=[],
            integration_patterns=[],
            implementation_steps=["Contact technical team for detailed assessment"],
            sources=[]
        )
    
    def add_integration_documents(self, documents: List[Dict[str, Any]]):
        """
        Add new integration documents to the knowledge base
        
        Args:
            documents: List of document dictionaries with 'content', 'title', 'type', etc.
        """
        
        print(f"📥 Adding {len(documents)} integration documents...")
        
        for doc_data in documents:
            # Determine target collection based on document type
            doc_type = doc_data.get("type", "integration_guide")
            collection_mapping = {
                "api": "api_specifications",
                "integration": "integration_guides", 
                "tutorial": "tutorials_examples",
                "glossary": "glossary_concepts",
                "use_case": "use_cases_patterns"
            }
            
            collection_name = collection_mapping.get(doc_type, "integration_guides")
            
            # Create document
            doc = Document(
                page_content=doc_data["content"],
                metadata={
                    "source_type": ContentType.INTEGRATION_GUIDE.value,
                    "title": doc_data.get("title", "Untitled"),
                    "complexity": doc_data.get("complexity", "medium"),
                    "integration_level": doc_data.get("integration_level", "application"),
                    "added_date": datetime.now().isoformat()
                }
            )
            
            # Add to appropriate collection
            self.vector_stores[collection_name].add_documents([doc])
        
        print(f"✅ Successfully added {len(documents)} documents to knowledge base")
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about each collection"""
        
        stats = {}
        for collection_name, collection in self.collections.items():
            stats[collection_name] = collection.count()
        
        return stats