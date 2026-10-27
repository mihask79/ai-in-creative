"""Variant 1 entry point; run from the LR08 folder. Trains all 16 models."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from lab08_experiment import run_all
from verify_artifacts import verify

if __name__=='__main__':
    run_all()
    verify()
