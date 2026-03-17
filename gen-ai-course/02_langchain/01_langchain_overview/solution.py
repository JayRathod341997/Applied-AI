"""
Solution: Getting Started with LangChain
This is the solution code for the first LangChain exercise.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser


def create_basic_chain():
    """Create a basic LangChain with prompt template."""

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        # API key can be set via environment variable: OPENAI_API_KEY
    )

    # Create a prompt template with dynamic inputs
    prompt = ChatPromptTemplate.from_template(
        "Tell me a {adjective} fact about {topic}"
    )

    # Create the chain using LCEL (LangChain Expression Language)
    # The | operator chains components together:
    # 1. prompt -> formats the input
    # 2. llm -> generates response
    # 3. StrOutputParser -> extracts string from response
    chain = prompt | llm | StrOutputParser()

    return chain


def create_with_messages():
    """Create a chain using ChatMessage templates."""

    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create a chat prompt template with multiple messages
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant specializing in {topic}."),
            ("human", "Can you tell me something interesting about {subject}?"),
        ]
    )

    # Chain with messages
    chain = chat_prompt | llm | StrOutputParser()

    return chain


def invoke_chain(chain, adjective, topic):
    """Invoke the chain with given parameters."""
    result = chain.invoke({"adjective": adjective, "topic": topic})
    return result


def invoke_with_messages(chain, topic, subject):
    """Invoke the chain with message parameters."""
    result = chain.invoke({"topic": topic, "subject": subject})
    return result


def main():
    """Main function to demonstrate the solution."""
    print("=" * 60)
    print("LangChain Basic Example - SOLUTION")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not found!")
        print("Please set your API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr add this to your code (not recommended for production):")
        print("  os.environ['OPENAI_API_KEY'] = 'your-key-here'")
        return

    # Create the chain
    print("\n1. Creating basic chain...")
    basic_chain = create_basic_chain()
    print("   ✓ Chain created successfully!")

    # Test basic chain
    print("\n2. Testing basic chain...")
    test_cases = [
        ("interesting", "artificial intelligence"),
        ("surprising", "space exploration"),
    ]

    for adjective, topic in test_cases:
        print(f"\n   Input: {adjective} fact about {topic}")
        result = invoke_chain(basic_chain, adjective, topic)
        # Print first 150 characters
        print(f"   Output: {result[:150]}...")

    # Create chat-based chain
    print("\n3. Creating chat message chain...")
    chat_chain = create_with_messages()
    print("   ✓ Chat chain created!")

    print("\n4. Testing chat chain...")
    result = invoke_with_messages(chat_chain, "science", "black holes")
    print(f"   Output: {result[:150]}...")

    print("\n" + "=" * 60)
    print("Solution completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
