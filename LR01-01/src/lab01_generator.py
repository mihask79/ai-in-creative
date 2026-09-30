"""Deterministic procedural grayscale texture generator for Lab 01."""

from __future__ import annotations

import math
import random
from array import array


def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def generate(size: int, cell: int, octaves: int, persistence: float, seed: int,
             interpolation: str = "smooth", bits: int = 8) -> bytes:
    """Return row-major 8-bit pixels using only the Python standard library."""
    if size <= 0 or cell <= 0 or octaves < 1 or not 1 <= bits <= 8:
        raise ValueError("size/cell must be positive; octaves >= 1; bits in 1..8")
    if interpolation not in {"smooth", "linear"}:
        raise ValueError("interpolation must be 'smooth' or 'linear'")

    rng = random.Random(seed)
    total = array("d", [0.0]) * (size * size)
    amplitude_sum = 0.0
    amplitude = 1.0
    for octave in range(octaves):
        step = max(1.0, cell / (2 ** octave))
        cols = math.ceil((size - 1) / step) + 2
        rows = math.ceil((size - 1) / step) + 2
        grid = [[rng.random() for _ in range(cols)] for _ in range(rows)]
        for y in range(size):
            gy = y / step
            iy = int(gy)
            fy = gy - iy
            vy = _smooth(fy) if interpolation == "smooth" else fy
            rowoff = y * size
            for x in range(size):
                gx = x / step
                ix = int(gx)
                fx = gx - ix
                vx = _smooth(fx) if interpolation == "smooth" else fx
                a = grid[iy][ix] * (1.0 - vx) + grid[iy][ix + 1] * vx
                b = grid[iy + 1][ix] * (1.0 - vx) + grid[iy + 1][ix + 1] * vx
                total[rowoff + x] += amplitude * (a * (1.0 - vy) + b * vy)
        amplitude_sum += amplitude
        amplitude *= persistence

    levels = (1 << bits) - 1
    out = bytearray(size * size)
    for i, value in enumerate(total):
        normalized = value / amplitude_sum
        quantized = round(normalized * levels) / levels
        out[i] = round(quantized * 255)
    return bytes(out)
