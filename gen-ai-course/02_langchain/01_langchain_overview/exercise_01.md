# Exercise 1: Getting Started with LangChain

## Objective

Set up a basic LangChain environment and create your first simple chain.

## Prerequisites

- Python 3.8+ installed
- OpenAI API key (or alternative LLM provider)
- Basic understanding of Python

## Instructions

### Step 1: Install LangChain

```bash
pip install langchain langchain-openai
```

### Step 2: Set Up Environment Variables

Create a `.env` file or set environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Step 3: Create a Simple Chain

Write a Python script that:
1. Imports the necessary LangChain components
2. Initializes a ChatOpenAI model
3. Creates a prompt template
4. Chains them together
5. Invokes the chain with input

### Step 4: Test Your Chain

Run your script and verify it returns a response.

## Expected Output

A working Python script that produces output from an LLM using LangChain.

## Deliverable

Submit your Python script (`exercise.py`) that demonstrates:
- LangChain installation and import
- Basic chain creation
- Successful invocation with output

## Time Estimate

15-20 minutes
