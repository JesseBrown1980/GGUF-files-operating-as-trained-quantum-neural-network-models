"""Run the stage B tests: python3 -I run_tests.py (isolated mode; this file puts reader/b on sys.path itself)."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(os.path.join(HERE, "tests"), top_level_dir=HERE)
    result = unittest.TextTestRunner(verbosity=int(os.environ.get("V", "1"))).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
