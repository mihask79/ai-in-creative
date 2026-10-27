"""Variant 1: Appendix A adapted for local CPU; Sobel is NumPy equivalent."""
import hashlib
import io
from pathlib import Path
import numpy as np
import torch
from diffusers import AutoPipelineForText2Image

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'stabilityai/sd-turbo'
REVISION = 'b261bac6fd2cf515557d5d0707481eafa0485ec2'
CLIP_ID = 'openai/clip-vit-base-patch32'
CLIP_REVISION = '3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268'
PROMPT = ('editorial poster concept for a robotics festival, glowing mechanical arm silhouette, '
          'deep blue and amber palette, clean composition, no text, no logo, no people')
SEEDS = list(range(101, 106))

def load_pipe():
    local = ROOT.parent/'LR05/.cache/huggingface/hub/models--stabilityai--sd-turbo/snapshots'/REVISION
    source = str(local) if local.exists() else MODEL_ID
    pipe = AutoPipelineForText2Image.from_pretrained(source, revision=REVISION,
        variant='fp16', torch_dtype=torch.float32, use_safetensors=True,
        cache_dir=str(ROOT/'.cache/huggingface'))
    pipe.to('cpu')
    # PyTorch SDPA uses the CPU's optimized attention implementation.
    pipe.disable_attention_slicing()
    pipe.set_progress_bar_config(disable=True)
    return pipe

def generate(pipe, seed, steps=1, guidance=0.0):
    return pipe(prompt=PROMPT, num_inference_steps=steps, guidance_scale=guidance,
        height=512, width=512, generator=torch.Generator('cpu').manual_seed(seed)).images[0]

def png_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def luma(img):
    a = np.asarray(img.convert('RGB'), dtype=np.float64)/255
    return a @ np.array([0.299, 0.587, 0.114])

def edge_energy(img):
    # scipy.ndimage.sobel default mode='reflect': half-sample symmetric padding.
    y = np.pad(luma(img), 1, mode='symmetric')
    gy = (y[2:, :-2]+2*y[2:, 1:-1]+y[2:, 2:]
          -y[:-2, :-2]-2*y[:-2, 1:-1]-y[:-2, 2:])
    gx = (y[:-2, 2:]+2*y[1:-1, 2:]+y[2:, 2:]
          -y[:-2, :-2]-2*y[1:-1, :-2]-y[2:, :-2])
    return float(np.mean(np.hypot(gx, gy)/8))

def contrast(img):
    return float(np.std(luma(img)))

def load_clip():
    from transformers import CLIPModel, CLIPProcessor
    path = ROOT/'.cache/clip'
    model = CLIPModel.from_pretrained(path, local_files_only=True).to('cpu').eval()
    processor = CLIPProcessor.from_pretrained(path, local_files_only=True, use_fast=False)
    return model, processor

@torch.no_grad()
def clip_sim(clip, image):
    model, processor = clip
    inputs = processor(text=[PROMPT], images=image, return_tensors='pt',
        padding=True, truncation=True, max_length=77)
    out = model(**inputs)
    a = out.image_embeds/out.image_embeds.norm(dim=-1, keepdim=True)
    b = out.text_embeds/out.text_embeds.norm(dim=-1, keepdim=True)
    return float((a*b).sum())*100

def summarize(measurements, pre):
    rows = []
    for key in ['clip', 'edge', 'contrast', 'seconds']:
        a = np.array([x[key] for x in measurements if x['mode']=='A'])
        b = np.array([x[key] for x in measurements if x['mode']=='B'])
        mean_a, mean_b, sd = float(a.mean()), float(b.mean()), float(a.std(ddof=1))
        d = mean_b-mean_a
        tol = pre['tolerance'][key]
        threshold = tol['value'] if tol['kind']=='absolute' else abs(mean_a)*tol['value']
        sign = -1 if key=='seconds' else 1
        classification = 'нейтрально' if abs(d)<=threshold else ('улучшение' if d*sign>0 else 'ухудшение')
        rows.append(dict(metric=key, A=mean_a, s=sd, B=mean_b, delta=d,
            ratio=abs(d)/sd if sd>0 else None, criterion_2s=bool(abs(d)>2*sd),
            percent=100*d/mean_a if mean_a else None, threshold=threshold,
            classification=classification, outside_tolerance=bool(abs(d)>threshold)))
    return rows
