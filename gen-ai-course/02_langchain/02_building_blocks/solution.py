"""
Solution: Building Blocks Exercise
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import JsonOutputParser
from pydantic import BaseModel


class Recipe(BaseModel):
    name: str
    ingredients: list
    instructions: list
    prep_time_minutes: int


def main():
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create prompt template with variables
    prompt = ChatPromptTemplate.from_template(
        "Generate a {cuisine} recipe with {difficulty} difficulty."
    )

    # Create JSON output parser
    parser = JsonOutputParser(pydantic_object=Recipe)

    # Create chain using LCEL
    chain = prompt | llm | parser

    # Invoke chain
    result = chain.invoke({"cuisine": "Italian", "difficulty": "medium"})

    print(f"Recipe: {result.get('name')}")
    print(f"Prep time: {result.get('prep_time_minutes')} minutes")


if __name__ == "__main__":
    main()
