"""
Exercise: Getting Started with LangChain
This script demonstrates creating a basic LangChain.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

# Set up API key
# Option 1: Set environment variable before running
# os.environ["OPENAI_API_KEY"] = "your-api-key"

# Option 2: Pass directly (not recommended for production)
# llm = ChatOpenAI(openai_api_key="your-api-key", model="gpt-4")


def create_basic_chain():
    """Create a basic LangChain with prompt template."""

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        # Uncomment if not using environment variable
        # openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create a prompt template
    prompt = ChatPromptTemplate.from_template(
        "Tell me a {adjective} fact about {topic}"
    )

    # Create the chain using LCEL (LangChain Expression Language)
    chain = prompt | llm | StrOutputParser()

    return chain


def invoke_chain(chain, adjective, topic):
    """Invoke the chain with given parameters."""
    result = chain.invoke({"adjective": adjective, "topic": topic})
    return result


def main():
    """Main function to run the exercise."""
    print("=" * 50)
    print("LangChain Basic Example")
    print("=" * 50)

    # Create the chain
    print("\n1. Creating the chain...")
    chain = create_basic_chain()
    print("   Chain created successfully!")

    # Invoke with different parameters
    print("\n2. Invoking chain with different inputs...")

    test_cases = [
        ("interesting", "artificial intelligence"),
        ("surprising", "space exploration"),
        ("fascinating", "quantum computing"),
    ]

    for adjective, topic in test_cases:
        print(f"\n   Input: {adjective} fact about {topic}")
        result = invoke_chain(chain, adjective, topic)
        print(f"   Output: {result[:200]}...")

    print("\n" + "=" * 50)
    print("Exercise completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
