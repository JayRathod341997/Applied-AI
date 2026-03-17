"""
Exercise: Production Patterns Solution
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache


def main():
    # Enable caching
    set_llm_cache(InMemoryCache())

    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    prompt = PromptTemplate.from_template("Tell me about {topic}")
    chain = prompt | llm

    # First call - will hit API
    result1 = chain.invoke({"topic": "AI"})

    # Second call - will use cache
    result2 = chain.invoke({"topic": "AI"})

    print(result1)
    print("Cached:", result1 == result2)


if __name__ == "__main__":
    main()
