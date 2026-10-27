"""Actual SD-Turbo experiment. Run from LR05 or import main from the notebook."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "180")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
import importlib.metadata as md
import torch
import lab05_lib as L

ART = ROOT / "artifacts"
def now():
    return datetime.now(timezone(timedelta(hours=3))).isoformat()
def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def main():
    ART.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    prereg = dict(recorded_at=now(), variant=1, brief="Афиша фестиваля робототехники",
        condition="repeat", seed=1001, model_id=L.MODEL_ID, revision=L.REVISION, prompt=L.PROMPT,
        steps=1, guidance_scale=0.0, size=512, generator_device="cpu", dtype="float32",
        hypothesis="Два последовательных вызова со свежим CPU-генератором и seed 1001 совпадут побитово.",
        tolerance_db=40.0, rule="identical: равные пиксели; close: PSNR >= 40 дБ; different: PSNR < 40 дБ",
        error_hypothesis="Повторное использование одного Generator изменит начальный шум и изображение.")
    save_json(ROOT / "configs" / "preregistration.json", prereg)
    print("Гипотеза и допуск записаны до загрузки модели:", prereg["recorded_at"], flush=True)
    print(prereg["hypothesis"], flush=True)
    env = dict(platform=platform.platform(), python=platform.python_version(), execution_device="cpu",
        cpu=platform.processor(), logical_cpus=os.cpu_count(), torch_num_threads=torch.get_num_threads(),
        cuda_available=torch.cuda.is_available(), deterministic_algorithms=True,
        packages={p: md.version(p) for p in ["torch", "diffusers", "transformers", "Pillow", "numpy", "accelerate", "safetensors"]})
    print(json.dumps(env, ensure_ascii=False, indent=2), flush=True)
    (ROOT / "reports" / "environment.txt").write_text(subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True) if md.packages_distributions().get("pip") else
        "\n".join(f"{p}=={v}" for p,v in env["packages"].items()), encoding="utf-8")
    t0 = time.perf_counter()
    pipe = L.load_pipe(ROOT / ".cache" / "huggingface" / "hub")
    load_s = time.perf_counter() - t0
    print(f"Модель загружена за {load_s:.2f} с. Прогрев...", flush=True)
    t0 = time.perf_counter()
    L.generate(pipe, seed=1)
    warm_s = time.perf_counter() - t0
    print(f"Прогрев: {warm_s:.2f} с", flush=True)
    manifests = {}
    def run(name, generator=None):
        before = None if generator is None else L.sha(bytes(generator.get_state().tolist()))
        t0 = time.perf_counter()
        image = L.generate(pipe, generator=generator)
        dt = time.perf_counter() - t0
        out = ART / name
        out.mkdir(exist_ok=True)
        raw = L.png_bytes(image)
        (out / "result.png").write_bytes(raw)
        manifest = {**prereg, **env, "created_at":now(), "run":name, "device":"cpu",
            "weight_variant":"fp16", "compute_dtype":"float32", "image_size":list(image.size),
            "image_mode":image.mode, "sha256":L.sha(raw), "load_seconds":load_s,
            "warmup_seconds":warm_s, "generation_seconds":dt,
            "generator_policy":"fresh_seed" if generator is None else "shared_state",
            "generator_state_before_sha256":before,
            "generator_state_after_sha256":None if generator is None else L.sha(bytes(generator.get_state().tolist()))}
        save_json(out / "manifest.json", manifest)
        manifests[name] = manifest
        print(f"{name}: {dt:.2f} с; SHA-256 {manifest['sha256']}", flush=True)
        return image
    a = run("run_A")
    b = run("run_B")
    shared = torch.Generator(device="cpu").manual_seed(1001)
    e1 = run("error_A", shared)
    e2 = run("error_B", shared)
    fixed = run("fixed")
    results = dict(variant=1, finished_at=now(), environment=env, preregistration=prereg,
        repeat=L.compare(a,b), shared_generator=L.compare(e1,e2),
        first_shared_vs_reference=L.compare(a,e1), repaired_vs_reference=L.compare(a,fixed),
        manifests=manifests, new_session_checked=False)
    save_json(ART / "results.json", results)
    passport = dict(date="2026-10-27", student="Скрыпник Михаил Дмитриевич", group="МИК11",
        variant=1, task="Повтор запуска SD-Turbo в одном сеансе", parameters=prereg,
        environment=env, load_seconds=load_s, warmup_seconds=warm_s,
        source_library="Приложение А, адаптация для CPU и сохранения всех артефактов",
        actual_environment="Локальный Python, Windows; Engee и Colab не использовались",
        reproducibility_scope="Один сеанс, один seed, CPU float32; иной GPU и новый сеанс не проверены",
        comparisons={k:results[k] for k in ["repeat","shared_generator","repaired_vs_reference"]})
    save_json(ART / "passport.json", passport)
    print(json.dumps({k:results[k] for k in ["repeat","shared_generator","first_shared_vs_reference","repaired_vs_reference"]}, ensure_ascii=False, indent=2), flush=True)
    return results

if __name__ == "__main__":
    main()
