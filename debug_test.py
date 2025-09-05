#!/usr/bin/env python3
"""
Debug script to test individual components
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello, this is a test. Reply with 'OpenAI working!'"}],
            max_tokens=10
        )

        print("✅ OpenAI Connection: SUCCESS")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI Connection: FAILED - {e}")
        return False


def test_api_docs_processor():
    """Test API documentation processor"""
    try:
        from components.api_docs_processor import APIDocsProcessor

        print("Testing API Documentation Processor...")
        processor = APIDocsProcessor()

        print(f"Knowledge base keys: {list(processor.knowledge_base.keys())}")

        if 'endpoints' in processor.knowledge_base:
            endpoint_count = len(processor.knowledge_base['endpoints'])
            print(f"✅ API Docs Processor: SUCCESS - {endpoint_count} endpoints loaded")
            return True
        else:
            print("❌ API Docs Processor: No endpoints loaded")
            return False

    except Exception as e:
        print(f"❌ API Docs Processor: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_analyzer():
    """Test intent analyzer with simple input"""
    try:
        from components.feasibility_analyzer import IntentAnalyzer

        analyzer = IntentAnalyzer()
        result = analyzer.analyze_intent("I want to create a contract from a template")

        if result:
            print("✅ Intent Analyzer: SUCCESS")
            print(f"Intent Category: {result.get('intent_category')}")
            print(f"Summary: {result.get('summary')}")
            print(f"Confidence: {result.get('confidence')}")
            return True
        else:
            print("❌ Intent Analyzer: No result returned")
            return False

    except Exception as e:
        print(f"❌ Intent Analyzer: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🔧 OneFlow API Helper - Component Testing\n")

    # Test environment setup
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment")
        return

    print(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')[:10]}..." + "*" * 20)
    print()

    # Run individual tests
    openai_ok = test_openai_connection()
    print()

    api_docs_ok = test_api_docs_processor()
    print()

    if openai_ok:
        intent_ok = test_intent_analyzer()
    else:
        intent_ok = False

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"OpenAI Connection: {'✅' if openai_ok else '❌'}")
    print(f"API Docs Processor: {'✅' if api_docs_ok else '❌'}")
    print(f"Intent Analyzer: {'✅' if intent_ok else '❌'}")


if __name__ == "__main__":
    main()