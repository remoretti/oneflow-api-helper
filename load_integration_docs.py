"""
Document Loader Script for OneFlow Integration Documents
Loads .doc, .docx, and .txt files into the enhanced knowledge base
"""

import os
import sys
from typing import List, Dict, Any

def load_text_file(file_path: str) -> str:
    """Load content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def load_docx_file(file_path: str) -> str:
    """Load content from a .docx file"""
    try:
        from docx import Document
        doc = Document(file_path)
        content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)
        
        return '\n'.join(content)
    except ImportError:
        print("❌ python-docx not installed. Run: pip install python-docx")
        return ""
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return ""

def load_doc_file(file_path: str) -> str:
    """Load content from a .doc file (older format)"""
    try:
        import subprocess
        # This is a fallback - .doc files are tricky
        # You might need to convert them to .docx first
        print(f"⚠️ .doc file detected: {file_path}")
        print("Consider converting .doc files to .docx or .txt for better compatibility")
        return f"[Document content from {os.path.basename(file_path)} - please convert to .txt or .docx format]"
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return ""

def determine_doc_type(filename: str, content: str) -> str:
    """Determine document type from filename and content"""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    # Check filename patterns first
    if any(keyword in filename_lower for keyword in ['api', 'endpoint', 'reference']):
        return 'api'
    elif any(keyword in filename_lower for keyword in ['tutorial', 'guide', 'howto', 'step']):
        return 'tutorial'
    elif any(keyword in filename_lower for keyword in ['glossary', 'definition', 'terms']):
        return 'glossary'
    elif any(keyword in filename_lower for keyword in ['usecase', 'use_case', 'scenario', 'example']):
        return 'use_case'
    
    # Check content patterns
    if any(keyword in content_lower for keyword in ['endpoint', 'api call', 'http', 'rest']):
        return 'api'
    elif any(keyword in content_lower for keyword in ['step 1', 'first step', 'tutorial', 'how to']):
        return 'tutorial'
    elif any(keyword in content_lower for keyword in ['definition:', 'means:', 'refers to']):
        return 'glossary'
    elif any(keyword in content_lower for keyword in ['use case', 'scenario', 'example']):
        return 'use_case'
    
    # Default to integration guide
    return 'integration'

def assess_complexity(content: str) -> str:
    """Assess document complexity based on length and content"""
    length = len(content)
    content_lower = content.lower()
    
    # Base complexity on length
    if length < 800:
        base_complexity = 'low'
    elif length < 3000:
        base_complexity = 'medium'
    else:
        base_complexity = 'high'
    
    # Adjust based on technical content
    technical_keywords = ['api', 'endpoint', 'json', 'webhook', 'authentication', 'oauth']
    technical_count = sum(1 for keyword in technical_keywords if keyword in content_lower)
    
    if technical_count >= 5:
        return 'high'
    elif technical_count >= 2 and base_complexity == 'low':
        return 'medium'
    
    return base_complexity

def determine_integration_level(content: str) -> str:
    """Determine integration level from content"""
    content_lower = content.lower()
    
    if any(keyword in content_lower for keyword in ['partner', 'marketplace', 'generic']):
        return 'partner'
    elif any(keyword in content_lower for keyword in ['application', 'crm', 'system integration']):
        return 'application'
    else:
        return 'standard'

def load_documents_from_folder(folder_path: str) -> List[Dict[str, Any]]:
    """Load all documents from a folder"""
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return []
    
    print(f"📂 Loading documents from: {folder_path}")
    
    documents = []
    supported_extensions = ['.txt', '.docx', '.doc', '.md']
    
    # Get all files in folder
    files = [f for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in supported_extensions)]
    
    if not files:
        print(f"❌ No supported files found in {folder_path}")
        print(f"   Looking for: {', '.join(supported_extensions)}")
        return []
    
    print(f"📄 Found {len(files)} documents to process")
    
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        
        try:
            # Load content based on file type
            if filename.lower().endswith('.txt', '.md'):
                content = load_text_file(file_path)
            elif filename.lower().endswith('.docx'):
                content = load_docx_file(file_path)
            elif filename.lower().endswith('.doc'):
                content = load_doc_file(file_path)
            else:
                continue
            
            # Skip empty files
            if not content or len(content.strip()) < 10:
                print(f"⚠️ Skipping empty file: {filename}")
                continue
            
            # Create document metadata
            title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
            doc_type = determine_doc_type(filename, content)
            complexity = assess_complexity(content)
            integration_level = determine_integration_level(content)
            
            document = {
                "content": content.strip(),
                "title": title,
                "type": doc_type,
                "complexity": complexity,
                "integration_level": integration_level,
                "filename": filename,
                "file_size": len(content)
            }
            
            documents.append(document)
            print(f"✅ Loaded: {filename} ({doc_type}, {complexity}) - {len(content)} chars")
            
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
    
    print(f"🎉 Successfully loaded {len(documents)} documents")
    return documents

def main():
    """Main function to load documents into knowledge base"""
    
    # Configuration
    DOCS_FOLDER = "./integration_documents"  # Change this to your folder path
    
    print("🚀 OneFlow Integration Documents Loader")
    print("=" * 50)
    
    # Check if enhanced analyzer is available
    try:
        from enhanced_feasibility_analyzer import EnhancedFeasibilityAnalyzer
        print("✅ Enhanced analyzer found")
    except ImportError as e:
        print(f"❌ Cannot import enhanced analyzer: {e}")
        print("Make sure enhanced_feasibility_analyzer.py is in the current directory")
        sys.exit(1)
    
    # Load documents
    documents = load_documents_from_folder(DOCS_FOLDER)
    
    if not documents:
        print("❌ No documents loaded. Exiting.")
        sys.exit(1)
    
    # Show summary
    print("\n📊 Document Summary:")
    print("-" * 30)
    
    type_counts = {}
    complexity_counts = {}
    
    for doc in documents:
        doc_type = doc['type']
        complexity = doc['complexity']
        
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
    
    print("By Type:")
    for doc_type, count in type_counts.items():
        print(f"  {doc_type}: {count}")
    
    print("By Complexity:")
    for complexity, count in complexity_counts.items():
        print(f"  {complexity}: {count}")
    
    # Confirm before loading
    response = input(f"\n🤔 Load {len(documents)} documents into knowledge base? (y/n): ")
    
    if response.lower() != 'y':
        print("❌ Cancelled by user")
        sys.exit(0)
    
    # Initialize enhanced analyzer and load documents
    try:
        print("\n🔧 Initializing Enhanced Analyzer...")
        analyzer = EnhancedFeasibilityAnalyzer(use_existing_api_processor=True)
        
        print("📥 Adding documents to knowledge base...")
        analyzer.add_integration_documents(documents)
        
        print("✅ Documents successfully added to knowledge base!")
        
        # Show final stats
        stats = analyzer.get_collection_stats()
        print("\n📈 Final Collection Statistics:")
        for collection, count in stats.items():
            collection_name = collection.replace('_', ' ').title()
            print(f"  {collection_name}: {count} documents")
        
        total = sum(stats.values())
        print(f"\n🎯 Total documents in knowledge base: {total}")
        
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()