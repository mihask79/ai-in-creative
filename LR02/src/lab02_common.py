"""Shared helpers for the reproducible variant 7 laboratory workflow."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
REPORTS = ROOT / 'reports'
NIST_GROUPS = {
    'CBRN Information or Capabilities', 'Confabulation',
    'Dangerous, Violent, or Hateful Content', 'Data Privacy',
    'Environmental Impacts', 'Harmful Bias or Homogenization',
    'Human-AI Configuration', 'Information Integrity',
    'Information Security', 'Intellectual Property',
    'Obscene, Degrading, and/or Abusive Content',
    'Value Chain and Component Integration',
}

def read_json(path):
    with open(path, encoding='utf-8') as f: return json.load(f)

def write_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def write_csv(path, fieldnames, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
