#!/usr/bin/env python3
"""
Simple OpenAI API test
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def test_openai():
    """Test OpenAI API with minimal request"""
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("❌ No API key found")
        return False

    print(f"🔑 API Key format: {api_key[:15]}...{api_key[-4:]}")

    try:
        client = OpenAI(api_key=api_key)

        # Use the cheapest model for testing
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper than gpt-4
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=5
        )

        print("✅ OpenAI API working!")
        print(f"Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False


if __name__ == "__main__":
    test_openai()