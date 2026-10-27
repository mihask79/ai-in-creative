"""Variant 1 helpers, adapted from Appendix A for local CPU execution."""
import hashlib
import io
import math
import numpy as np
import torch
from diffusers import AutoPipelineForText2Image

MODEL_ID = "stabilityai/sd-turbo"
REVISION = "b261bac6fd2cf515557d5d0707481eafa0485ec2"
PROMPT = ("editorial poster concept for a robotics festival, glowing mechanical arm silhouette, "
          "deep blue and amber palette, clean composition, no text, no logo, no people")

def load_pipe(cache_dir):
    # Same fp16 snapshot as the assignment, explicitly converted to float32 for CPU.
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID, revision=REVISION, variant="fp16", torch_dtype=torch.float32,
        use_safetensors=True, cache_dir=str(cache_dir))
    pipe.to("cpu")
    pipe.enable_attention_slicing()
    pipe.set_progress_bar_config(disable=True)
    return pipe

def generate(pipe, seed=1001, generator=None):
    if generator is None:
        generator = torch.Generator(device="cpu").manual_seed(seed)
    return pipe(prompt=PROMPT, num_inference_steps=1, guidance_scale=0.0,
                height=512, width=512, generator=generator).images[0]

def png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def compare(a, b, tolerance=40.0):
    aa = np.asarray(a.convert("RGB"), dtype=np.float64)
    bb = np.asarray(b.convert("RGB"), dtype=np.float64)
    delta = aa - bb
    mse = float(np.mean(delta ** 2))
    psnr = math.inf if mse == 0 else 10 * math.log10(255.0 ** 2 / mse)
    return dict(sha_a=sha(png_bytes(a)), sha_b=sha(png_bytes(b)),
                sha_equal=png_bytes(a) == png_bytes(b), pixel_equal=bool(np.array_equal(aa, bb)),
                max_diff=int(np.max(np.abs(delta))), mse=mse,
                psnr_db="Infinity" if mse == 0 else psnr, tolerance_db=tolerance,
                verdict="identical" if mse == 0 else "close" if psnr >= tolerance else "different")
