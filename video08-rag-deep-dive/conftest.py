# Test setup for this project only: imports resolve from this folder, and tests never
# call the model or touch the replay cache.
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["DEMO_CACHE"] = "off"
