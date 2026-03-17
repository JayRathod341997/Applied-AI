"""
Solution: Production Patterns Exercise
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache


def create_production_chain():
    """Create a production-ready chain with caching."""
    # Enable caching
    set_llm_cache(InMemoryCache())

    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    prompt = PromptTemplate.from_template("Tell me about {topic}")

    return prompt | llm


if __name__ == "__main__":
    chain = create_production_chain()

    # First call - hits API
    result1 = chain.invoke({"topic": "Machine Learning"})
    print("First call:", result1[:50])

    # Second call - uses cache
    result2 = chain.invoke({"topic": "Machine Learning"})
    print("Cached:", result1 == result2)
