"""Python implementation of laboratory work 3, variant 7.

The course library lab03_lib.jl was not present in the project, so the scene
generator below follows the written low-contrast parameters and is documented
as an equivalent implementation, not a byte-for-byte Engee reproduction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "artifacts"
SIZE = 128
LO, HI, NOISE_STD = 0.40, 0.60, 0.02
SEEDS = list(range(101, 106))
BINS = 32
PRACTICAL_RELATIVE_LIMIT = 0.05
PRACTICAL_PSNR_LIMIT_DB = 30.0


def make_scene(seed: int) -> np.ndarray:
    """Return a 128x128 RGB Float64 low-contrast synthetic scene.

    A stable smooth field and simple geometric forms provide scene structure;
    the seed changes only the additive Gaussian noise.
    """
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    x /= SIZE - 1
    y /= SIZE - 1
    field = 0.47 + 0.045 * (x - 0.5) + 0.035 * (0.5 - y)
    disk = ((x - 0.34) ** 2 + (y - 0.38) ** 2) < 0.13 ** 2
    bar = (x > 0.58) & (x < 0.79) & (y > 0.28) & (y < 0.72)
    field[disk] += 0.055
    field[bar] -= 0.045
    rng = np.random.default_rng(seed)
    gray = np.clip(field + rng.normal(0.0, NOISE_STD, (SIZE, SIZE)), LO, HI)
    # Small channel offsets make the source a color image while preserving its
    # low-contrast range. The offsets are fixed; only the noise depends on seed.
    rgb = np.stack((gray + 0.002, gray, gray - 0.002), axis=-1)
    return np.clip(rgb, LO, HI).astype(np.float64)


def luma_manual(rgb: np.ndarray) -> np.ndarray:
    return (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.float64)


def luma_gray(rgb: np.ndarray) -> np.ndarray:
    # Independent channel-array expression corresponding to an image Gray conversion.
    channels = np.moveaxis(rgb, -1, 0)
    return np.einsum("i,ijk->jk", np.array([0.299, 0.587, 0.114]), channels).astype(np.float64)


def array_sha(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array, dtype=np.float64).tobytes()).hexdigest()


def quantize_4bit(luma: np.ndarray) -> np.ndarray:
    return np.round(np.clip(luma, 0.0, 1.0) * 15.0) / 15.0


def metrics(luma: np.ndarray) -> dict[str, float]:
    hist, _ = np.histogram(luma, bins=BINS, range=(0.0, 1.0))
    p = hist[hist > 0] / hist.sum()
    entropy = float(-np.sum(p * np.log2(p)))
    return {
        "mean": float(np.mean(luma)),
        "contrast_std": float(np.std(luma, ddof=1)),
        "entropy_bits": entropy,
    }


def psnr(reference: np.ndarray, altered: np.ndarray) -> float:
    mse = float(np.mean((reference - altered) ** 2))
    return math.inf if mse == 0 else 10.0 * math.log10(1.0 / mse)


def font(size: int = 16) -> ImageFont.ImageFont:
    for candidate in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def save_gray(array: np.ndarray, path: Path) -> None:
    image = Image.fromarray(np.uint8(np.clip(array, 0, 1) * 255), mode="L")
    image.resize((512, 512), Image.Resampling.NEAREST).save(path)


def save_histogram(before: np.ndarray, after: np.ndarray, path: Path) -> None:
    w, h = 1000, 570
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    f = font(18)
    d.text((28, 18), "Variant 7: brightness histograms (32 bins)", fill="#172033", font=font(24))
    for panel, (arr, title, color) in enumerate(((before, "Before", "#4976c8"), (after, "After 4-bit quantization", "#d57935"))):
        top = 78 + panel * 238
        left, right, bottom = 92, 952, top + 176
        d.text((left, top - 29), title, fill="#172033", font=f)
        d.line((left, top, left, bottom, right, bottom), fill="#536174", width=2)
        hist, _ = np.histogram(arr, bins=BINS, range=(0, 1))
        maxv = max(int(hist.max()), 1)
        bw = (right - left) / BINS
        for i, value in enumerate(hist):
            x0 = left + i * bw + 1
            y0 = bottom - (bottom - top) * int(value) / maxv
            d.rectangle((x0, y0, left + (i + 1) * bw - 1, bottom), fill=color)
        d.text((left, bottom + 8), "0", fill="#536174", font=f)
        d.text((right - 12, bottom + 8), "1", fill="#536174", font=f)
    im.save(path)


def save_metric_plot(rows: list[dict], path: Path) -> None:
    w, h = 1000, 540
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    d.text((28, 18), "Baseline and quantized metrics across five seeds", fill="#172033", font=font(23))
    keys = [("mean", "Mean brightness"), ("contrast_std", "Contrast (std)"), ("entropy_bits", "Histogram entropy (bits)")]
    colors = ("#4976c8", "#d57935")
    base_x, top, plot_h, group_w = 115, 90, 350, 270
    for g, (key, label) in enumerate(keys):
        vals = [r[f"base_{key}"] for r in rows] + [r[f"after_{key}"] for r in rows]
        lo, hi = min(vals), max(vals)
        pad = max((hi - lo) * 0.16, 0.01)
        lo, hi = lo - pad, hi + pad
        gx = base_x + g * group_w
        d.text((gx, 55), label, fill="#172033", font=font(16))
        d.line((gx, top + plot_h, gx + 220, top + plot_h), fill="#536174", width=2)
        for i, subset in enumerate(("base", "after")):
            vals_i = [r[f"{subset}_{key}"] for r in rows]
            mean_v = float(np.mean(vals_i))
            sd = float(np.std(vals_i, ddof=1))
            y = top + plot_h - (mean_v - lo) / (hi - lo) * plot_h
            x = gx + 72 + i * 88
            d.rectangle((x - 18, y, x + 18, top + plot_h), fill=colors[i])
            yhi = top + plot_h - (mean_v + sd - lo) / (hi - lo) * plot_h
            ylo = top + plot_h - (mean_v - sd - lo) / (hi - lo) * plot_h
            d.line((x, yhi, x, ylo), fill="#172033", width=3)
            d.text((x - 30, top + plot_h + 10), "base" if i == 0 else "after", fill="#536174", font=font(14))
    d.text((95, 495), "Bars: mean across seeds; whiskers: sample standard deviation", fill="#536174", font=font(16))
    im.save(path)


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    baseline, altered = [], []
    max_luma_difference = 0.0
    first_hash = None
    for seed in SEEDS:
        rgb = make_scene(seed)
        a = luma_manual(rgb)
        b = luma_gray(rgb)
        max_luma_difference = max(max_luma_difference, float(np.max(np.abs(a - b))))
        if seed == SEEDS[0]:
            first_hash = array_sha(a)
            assert first_hash == array_sha(luma_manual(make_scene(seed)))
            save_gray(a, out / "scene_before.png")
            save_gray(quantize_4bit(a), out / "scene_after.png")
            save_histogram(a, quantize_4bit(a), out / "histograms.png")
        baseline.append(metrics(a))
        altered.append(metrics(quantize_4bit(a)))

    rows = []
    for idx, seed in enumerate(SEEDS):
        before, after = baseline[idx], altered[idx]
        record = {"seed": seed}
        for key in before:
            record[f"base_{key}"] = before[key]
            record[f"after_{key}"] = after[key]
            record[f"delta_{key}"] = after[key] - before[key]
        record["psnr_db"] = psnr(luma_manual(make_scene(seed)), quantize_4bit(luma_manual(make_scene(seed))))
        rows.append(record)

    summary = {}
    for key in baseline[0]:
        bvals = np.array([x[key] for x in baseline], dtype=float)
        avals = np.array([x[key] for x in altered], dtype=float)
        bmean, amean = float(bvals.mean()), float(avals.mean())
        sd = float(bvals.std(ddof=1))
        delta = amean - bmean
        ratio = abs(delta) / sd if sd else (math.inf if delta else 0.0)
        relative = abs(delta) / abs(bmean) if bmean else math.inf
        summary[key] = {
            "baseline_mean": bmean, "baseline_sd": sd,
            "after_mean": amean, "after_sd": float(avals.std(ddof=1)),
            "delta": delta, "relative_change": relative,
            "statistical_ratio_abs_delta_over_baseline_sd": ratio,
            "statistically_significant_by_course_rule": ratio > 2.0,
            "practically_significant_by_5_percent_rule": relative > PRACTICAL_RELATIVE_LIMIT,
        }
    mean_psnr = float(np.mean([r["psnr_db"] for r in rows]))
    save_metric_plot(rows, out / "metric_comparison.png")

    fields = list(rows[0])
    with (out / "metrics_by_seed.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "lab": "LR03", "variant": 7,
        "scene": {"name": "low contrast", "lo": LO, "hi": HI, "noise_std": NOISE_STD,
                  "shape_rgb": [SIZE, SIZE, 3], "dtype": "float64"},
        "operation": {"name": "4-bit luminance quantization", "levels": 16},
        "seeds": SEEDS, "histogram_bins": BINS,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "pillow": Image.__version__},
        "method": "Standalone Python equivalent. Scene geometry is authored in this project because lab03_lib.jl was not supplied.",
        "luma_max_abs_difference": max_luma_difference,
        "seed_101_luma_sha256": first_hash,
        "seed_101_checksum_reproduced": True,
        "metrics": summary,
        "mean_psnr_db": mean_psnr,
        "psnr_practical_limit_db": PRACTICAL_PSNR_LIMIT_DB,
        "psnr_practically_significant": mean_psnr < PRACTICAL_PSNR_LIMIT_DB,
        "raw_results": rows,
    }
    sample_scene = make_scene(SEEDS[0])
    result["scene"]["observed_min_seed_101"] = float(sample_scene.min())
    result["scene"]["observed_max_seed_101"] = float(sample_scene.max())
    (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    passport = {
        "laboratory": "ЛР03",
        "variant": 7,
        "date": __import__("datetime").date.today().isoformat(),
        "environment": result["environment"],
        "language_implementation": "Python",
        "scene": result["scene"],
        "seeds": SEEDS,
        "intervention": result["operation"],
        "histogram_bins": BINS,
        "practical_allowance": {"relative_metric_change_over": PRACTICAL_RELATIVE_LIMIT, "psnr_below_db": PRACTICAL_PSNR_LIMIT_DB},
        "sha256_luminance_seed_101": first_hash,
        "checksum_reproduced": True,
    }
    (out / "passport_lr03.json").write_text(json.dumps(passport, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(run(args.out), ensure_ascii=False, indent=2))
