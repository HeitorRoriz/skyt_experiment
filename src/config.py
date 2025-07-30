import os

# OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Model and temperature settings
MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.7  # Change here to experiment with different temperatures

# Experiment settings
NUM_RUNS = 5
MAX_ATTEMPTS = 3
DELAY_SECONDS = 2

# File paths
RESULTS_FILE = "outputs/results.xlsx"
EXPERIMENT_MATRIX_FILE = "outputs/experiment_matrix.xlsx"

# Prompt contract settings
USE_PROMPT_CONTRACT = False  # Set to False to use simple prompts without contract structure

# Experiment templates (prompts)
EXPERIMENT_TEMPLATES = [
    {"prompt": "Write a Python function to generate the first 20 Fibonacci numbers."},
    {"prompt": "Write a Python function that returns the first 20 Fibonacci numbers using recursion."},
    {"prompt": "Generate Python code to compute the first 20 Fibonacci numbers and return them as a list."},
    {"prompt": "Create a Python function named fibonacci that outputs the first 20 Fibonacci numbers."},
    {"prompt": "Implement a recursive Python function to produce the first 20 Fibonacci numbers."},
] 