"""
Solution: Chat Models and Chains Exercise
"""

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate


def create_sequential_chain():
    """Create a sequential chain for facts and summary."""
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Chain 1: Generate facts
    facts_prompt = PromptTemplate(
        input_variables=["topic"], template="List 3 interesting facts about {topic}"
    )
    facts_chain = LLMChain(llm=llm, prompt=facts_prompt, output_key="facts")

    # Chain 2: Summarize
    summary_prompt = PromptTemplate(
        input_variables=["facts"],
        template="Summarize these facts into one sentence: {facts}",
    )
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt, output_key="summary")

    # Sequential chain
    return SequentialChain(
        chains=[facts_chain, summary_chain],
        input_variables=["topic"],
        output_variables=["facts", "summary"],
    )


if __name__ == "__main__":
    chain = create_sequential_chain()
    result = chain.invoke({"topic": "machine learning"})
    print("Facts:", result["facts"])
    print("Summary:", result["summary"])
