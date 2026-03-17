"""
Exercise: Chat Models and Chains Solution
"""

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate


def main():
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Chain 1: Generate facts
    facts_prompt = PromptTemplate(
        input_variables=["topic"], template="List 3 interesting facts about {topic}"
    )
    facts_chain = LLMChain(llm=llm, prompt=facts_prompt, output_key="facts")

    # Chain 2: Summarize facts
    summary_prompt = PromptTemplate(
        input_variables=["facts"],
        template="Summarize these facts into one sentence: {facts}",
    )
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt, output_key="summary")

    # Sequential chain
    sequential_chain = SequentialChain(
        chains=[facts_chain, summary_chain],
        input_variables=["topic"],
        output_variables=["facts", "summary"],
    )

    # Invoke
    result = sequential_chain.invoke({"topic": "artificial intelligence"})
    print(f"Facts: {result['facts']}")
    print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    main()
