"""
Exercise: Memory, Tools, and Agents Solution
"""

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentType, initialize_agent
from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create agent with tools and memory
    agent = initialize_agent(
        tools=[calculator],
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
    )

    # Test agent
    result = agent.invoke("What is 5 + 3?")
    print(result)


if __name__ == "__main__":
    main()
