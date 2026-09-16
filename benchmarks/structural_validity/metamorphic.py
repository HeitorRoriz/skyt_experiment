"""Compatibility shim."""

from benchmark.validity.metamorphic import *  # noqa: F403
from benchmark.validity.metamorphic import ALL_CASES, evaluate, main  # noqa: F401

if __name__ == "__main__":
    main()
