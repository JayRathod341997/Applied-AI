"""
Solution: Memory, Tools, and Agents Exercise
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


def create_agent_with_memory():
    """Create an agent with memory and tools."""
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    agent = initialize_agent(
        tools=[calculator],
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
    )

    return agent


if __name__ == "__main__":
    agent = create_agent_with_memory()
    result = agent.invoke("What is 10 + 5?")
    print(result)
