"""Demonstrate the Lab 01 failure caused by omitting a seed."""
from __future__ import annotations

import argparse
import hashlib
import time
import warnings

from lab01_generator import generate

parser = argparse.ArgumentParser()
parser.add_argument("--seed", type=int)
args = parser.parse_args()
if args.seed is None:
    seed = time.time_ns() % (2**32)
    warnings.warn(f"--seed omitted; using time-derived seed {seed}", RuntimeWarning)
else:
    seed = args.seed
pixels = generate(size=96, cell=32, octaves=4, persistence=0.50, seed=seed)
print(f"seed={seed} sha256={hashlib.sha256(pixels).hexdigest()}")
