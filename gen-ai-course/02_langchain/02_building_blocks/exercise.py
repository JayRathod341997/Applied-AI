"""
Exercise: Building Blocks - Solution
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import JsonOutputParser
from pydantic import BaseModel


class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    instructions: list[str]
    prep_time_minutes: int


def main():
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        "Generate a {cuisine} recipe with {difficulty} difficulty."
    )

    # Create parser
    parser = JsonOutputParser(pydantic_object=Recipe)

    # Create chain
    chain = prompt | llm | parser

    # Invoke
    result = chain.invoke({"cuisine": "Italian", "difficulty": "medium"})

    print(result)


if __name__ == "__main__":
    main()
