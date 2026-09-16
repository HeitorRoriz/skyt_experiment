"""Compatibility shim. Table 2 lives in ``skyt.table2``."""

from skyt.table2 import *  # noqa: F403
from skyt.table2 import main  # noqa: F401

if __name__ == "__main__":
    main()
