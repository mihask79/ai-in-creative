"""Run reproducibility and one-factor tests for Lab 01."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import struct
import sys
import zlib
from pathlib import Path

from lab01_generator import generate


def png_gray(pixels: bytes, size: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)
    raw = b"".join(b"\0" + pixels[y * size:(y + 1) * size] for y in range(size))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def metrics(pixels: bytes, size: int) -> dict[str, float]:
    values = [v / 255.0 for v in pixels]
    hist = [0] * 256
    for v in pixels:
        hist[v] += 1
    n = len(values)
    mean = statistics.fmean(values)
    contrast = statistics.pstdev(values)
    edge = sum(abs(pixels[y * size + x] - pixels[y * size + x - 1])
               for y in range(size) for x in range(1, size)) / (size * (size - 1) * 255)
    entropy = -sum((c / n) * math.log2(c / n) for c in hist if c)
    return {"mean": mean, "contrast": contrast, "edge_energy": edge, "entropy_bits": entropy}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    if args.variant != 7:
        parser.error("this delivered run is configured for variant 7")
    args.out.mkdir(parents=True, exist_ok=True)

    # Variant 7: paper texture; factor: image size x1.5, 96 -> 144.
    common = {"size": 96, "octaves": 3, "persistence": 0.60, "bits": 8,
              "interpolation": "smooth"}
    baseline = {**common, "cell": 4}
    changed = {**common, "size": 144, "cell": 4}

    check_seeds = [101, 101, 1101, 101]
    check_arrays = [generate(**baseline, seed=s) for s in check_seeds]
    digests = [hashlib.sha256(p).hexdigest() for p in check_arrays]
    reproducibility = {"EQ_1_2": digests[0] == digests[1],
                       "EQ_1_4": digests[0] == digests[3],
                       "EQ_1_3": digests[0] == digests[2],
                       "EQ_2_4": digests[1] == digests[3]}

    # Save base/factor comparison images for the same seed and pixel hash.
    for label, params in (("baseline_seed101", baseline), ("factor_seed101", changed)):
        px = generate(**params, seed=101)
        (args.out / f"{label}.png").write_bytes(png_gray(px, params["size"]))

    seeds = list(range(101, 106))
    samples = {"baseline": {m: [] for m in metrics(check_arrays[0], 96)},
               "factor": {m: [] for m in metrics(check_arrays[0], 96)}}
    for seed in seeds:
        for name, params in (("baseline", baseline), ("factor", changed)):
            result = metrics(generate(**params, seed=seed), params["size"])
            for key, value in result.items():
                samples[name][key].append(value)

    summary = {}
    for key in samples["baseline"]:
        bmean = statistics.fmean(samples["baseline"][key])
        bsd = statistics.stdev(samples["baseline"][key])
        fmean = statistics.fmean(samples["factor"][key])
        delta = fmean - bmean
        ratio = abs(delta) / bsd if bsd else math.inf
        summary[key] = {"baseline_mean": bmean, "baseline_sample_sd": bsd,
                        "factor_mean": fmean, "delta": delta,
                        "abs_delta_over_baseline_sd": ratio,
                        "substantial_at_threshold_2": ratio > 2.0,
                        "factor_sample_sd": statistics.stdev(samples["factor"][key])}

    report = {"variant": 7, "context": "paper texture", "factor": "image size x1.5, 96 to 144",
              "threshold": 2.0, "seeds": seeds, "parameters": {"baseline": baseline, "factor": changed},
              "reproducibility": reproducibility,
              "pixel_sha256_prefix16": digests,
              "png_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in args.out.glob("*.png")},
              "metrics": summary, "environment": {"python": sys.version,
              "implementation": platform.python_implementation(), "platform": platform.platform(),
              "zlib": zlib.ZLIB_VERSION}}
    (args.out / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
