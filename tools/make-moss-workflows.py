#!/usr/bin/env python3
"""Derive the default MOSS-Image workflows from the Anima ones.

Writes workflows/moss-{txt2img,img2img,inpainting}-minworkflow-cads.json from
workflows/{mode}-minworkflow-cads.json. Node ids are kept, so the MOSS functional
workflow uses the same mappings as Anima. Changes:
  - MOSS UNET / Qwen3.5 text encoder (type moss_image) / FLUX.2 small VAE
  - EmptyFlux2LatentImage for txt2img
  - KSampler 25 steps, CFG 2.5, er_sde, simple (ComfyUI's MOSS template settings)
  - Skip Layer Guidance: LoRA -> SkipLayerGuidanceDiTSimple (#64) and a
    ComfySwitchNode (#65, off by default) choosing between them -> CADS

Usage: python3 tools/make-moss-workflows.py, then python3 tools/embed-workflows.py
"""
import json
import pathlib
import uuid

root = pathlib.Path(__file__).resolve().parent.parent
HF = "https://huggingface.co/Comfy-Org/MOSS-Image/resolve/main"
UNET = "models/MOSS/moss_image_sft_int8_convrot.safetensors"
CLIP = "models/MOSS/qwen3.5_9b_w4a8_gptq.safetensors"
VAE = "models/flux2/flux2-vae_small.safetensors"
SLG_ID, SWITCH_ID = 64, 65


def node(wf, nid):
    return next(n for n in wf["nodes"] if n["id"] == nid)


def set_widgets(n, **vals):
    n["widgets_values_named"].update(vals)
    n["widgets_values"] = [v for k, v in n["widgets_values_named"].items()]


def models_prop(n, name, directory):
    n["properties"]["models"] = [{"name": name, "url": f"{HF}/{directory}/{name}", "directory": directory}]


def convert(wf, mode):
    wf = json.loads(json.dumps(wf))
    wf["id"] = str(uuid.uuid4())

    unet = node(wf, 44)
    set_widgets(unet, unet_name=UNET)
    models_prop(unet, "moss_image_sft_int8_convrot.safetensors", "diffusion_models")
    clip = node(wf, 45)
    set_widgets(clip, clip_name=CLIP, type="moss_image")
    models_prop(clip, "qwen3.5_9b_w4a8_gptq.safetensors", "text_encoders")
    vae = node(wf, 15)
    set_widgets(vae, vae_name=VAE)
    models_prop(vae, "flux2-vae_small.safetensors", "vae")
    set_widgets(node(wf, 49), lora_name="moss_image_lora.safetensors")
    set_widgets(node(wf, 19), steps=25, cfg=2.5, sampler_name="er_sde", scheduler="simple")
    set_widgets(node(wf, 46), filename_prefix="%date:yyyyMMdd%/MOSS_%date:yyyyMMdd%")
    if mode == "txt2img":
        lat = node(wf, 28)
        lat["type"] = "EmptyFlux2LatentImage"
        lat["properties"]["Node name for S&R"] = "EmptyFlux2LatentImage"

    # Splice SLG + switch between the LoRA (#49) and CADS (#63).
    lora, cads = node(wf, 49), node(wf, 63)
    lid = wf["last_link_id"]
    l_lora_sw, l_lora_slg, l_slg_sw, l_sw_cads = lid + 1, lid + 2, lid + 3, lid + 4
    old = cads["inputs"][0]["link"]
    wf["links"] = [l for l in wf["links"] if l[0] != old]
    wf["links"] += [
        [l_lora_sw, 49, 0, SWITCH_ID, 0, "MODEL"],
        [l_lora_slg, 49, 0, SLG_ID, 0, "MODEL"],
        [l_slg_sw, SLG_ID, 0, SWITCH_ID, 1, "MODEL"],
        [l_sw_cads, SWITCH_ID, 0, 63, 0, "MODEL"],
    ]
    lora["outputs"][0]["links"] = [l_lora_sw, l_lora_slg]
    cads["inputs"][0]["link"] = l_sw_cads
    x, y = lora["pos"]
    order = max(n["order"] for n in wf["nodes"]) + 1
    wf["nodes"] += [{
        "id": SLG_ID, "type": "SkipLayerGuidanceDiTSimple", "pos": [x + 320, y - 260], "size": [300, 160],
        "flags": {}, "order": order, "mode": 0,
        "inputs": [{"name": "model", "type": "MODEL", "link": l_lora_slg}],
        "outputs": [{"name": "MODEL", "type": "MODEL", "links": [l_slg_sw]}],
        "properties": {"Node name for S&R": "SkipLayerGuidanceDiTSimple"},
        "widgets_values": ["", "22", 0, 0.5],
        "widgets_values_named": {"double_layers": "", "single_layers": "22", "start_percent": 0, "end_percent": 0.5},
    }, {
        "id": SWITCH_ID, "type": "ComfySwitchNode", "pos": [x + 320, y - 60], "size": [270, 110],
        "flags": {}, "order": order + 1, "mode": 0, "title": "SLG on/off",
        "inputs": [
            {"name": "on_false", "shape": 7, "type": "MODEL", "link": l_lora_sw},
            {"name": "on_true", "shape": 7, "type": "MODEL", "link": l_slg_sw},
            {"name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None},
        ],
        "outputs": [{"name": "output", "type": "MODEL", "links": [l_sw_cads]}],
        "properties": {"Node name for S&R": "ComfySwitchNode"},
        "widgets_values": [False],
        "widgets_values_named": {"switch": False},
    }]
    cads["order"] = order + 2
    node(wf, 19)["order"] = order + 3
    node(wf, 8)["order"] = order + 4
    node(wf, 46)["order"] = order + 5
    wf["last_node_id"] = max(wf["last_node_id"], SWITCH_ID)
    wf["last_link_id"] = l_sw_cads
    return wf


for mode in ("txt2img", "img2img", "inpainting"):
    src = json.loads((root / "workflows" / f"{mode}-minworkflow-cads.json").read_text())
    out = root / "workflows" / f"moss-{mode}-minworkflow-cads.json"
    out.write_text(json.dumps(convert(src, mode), indent=2) + "\n")
    print(f"Wrote {out.relative_to(root)}")
