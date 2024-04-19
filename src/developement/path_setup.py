import sys
import os
from pathlib import Path

src_dir = os.path.abspath(Path(__file__).parents[1])
root_dir = os.path.abspath(Path(__file__).parents[1])

sys.path.insert(0, src_dir)
sys.path.insert(0, root_dir)