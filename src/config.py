import os

# =============================================================================
# LLM Provider Configuration
# =============================================================================

# Provider selection: "openai", "anthropic", "openrouter"
LLM_PROVIDER = os.environ.get("SKYT_PROVIDER", "openai")

# API Keys (provider-specific)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Model selection (provider-specific defaults if not set)
MODEL = os.environ.get("SKYT_MODEL")  # None = use provider default

# Default models by provider
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openrouter": "anthropic/claude-3.5-sonnet",
}

# =============================================================================
# Core Configuration
# =============================================================================

METRICS_VERSION = "2025-09-29"
TEMPERATURE = float(os.environ.get("SKYT_TEMPERATURE", "0.0"))

# Experiment configuration
TARGET_RUNS_PER_PROMPT = 5
OUTPUT_DIR_TEMPLATE = "outputs/temp_{temperature}"

# Simplified SKYT - Focus on core metrics
CORE_METRICS = ["R_raw", "R_canon"]
DEFAULT_ALGORITHM = "fibonacci"

# Paths
CONTRACTS_DIR = "contracts"
OUTPUTS_DIR = "outputs"
RESULTS_FILE = "results.csv"


# =============================================================================
# Helper Functions
# =============================================================================

def get_model_for_provider(provider: str = None) -> str:
    """Get model name for given provider (or current provider)"""
    provider = provider or LLM_PROVIDER
    return MODEL or DEFAULT_MODELS.get(provider, "gpt-4o-mini")


def get_api_key_for_provider(provider: str = None) -> str:
    """Get API key for given provider (or current provider)"""
    provider = provider or LLM_PROVIDER
    keys = {
        "openai": OPENAI_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "openrouter": OPENROUTER_API_KEY,
    }
    return keys.get(provider)
