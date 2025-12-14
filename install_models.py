import os
import sys
import torch
import layoutparser as lp
from unittest.mock import patch
from transformers import AutoModelForCausalLM, AutoProcessor
from transformers.dynamic_module_utils import get_imports

# --- PATHS ---
PROJECT_ROOT = os.getcwd()
MODEL_DIR = os.path.join(PROJECT_ROOT, "src", "models", "layoutparser")
os.makedirs(MODEL_DIR, exist_ok=True)

LOCAL_CONFIG = os.path.join(MODEL_DIR, "config.yml")
LOCAL_WEIGHTS = os.path.join(MODEL_DIR, "model_final.pth")

# --- 1. LAYOUTPARSER SETUP ---


def setup_layoutparser():
    print("\n--- 1. SETTING UP LAYOUTPARSER ---")

    # A. Write the Config File Manually (Avoids download corruption)
    # This is the standard PubLayNet Faster-RCNN config
    config_content = """
MODEL:
  META_ARCHITECTURE: "GeneralizedRCNN"
  BACKBONE:
    NAME: "build_resnet_fpn_backbone"
  RESNETS:
    OUT_FEATURES: ["res2", "res3", "res4", "res5"]
    DEPTH: 50
  FPN:
    IN_FEATURES: ["res2", "res3", "res4", "res5"]
  ANCHOR_GENERATOR:
    SIZES: [[32], [64], [128], [256], [512]]
    ASPECT_RATIOS: [[0.5, 1.0, 2.0]]
  RPN:
    IN_FEATURES: ["p2", "p3", "p4", "p5", "p6"]
    PRE_NMS_TOPK_TRAIN: 2000
    PRE_NMS_TOPK_TEST: 1000
    POST_NMS_TOPK_TRAIN: 1000
    POST_NMS_TOPK_TEST: 1000
  ROI_HEADS:
    NAME: "StandardROIHeads"
    IN_FEATURES: ["p2", "p3", "p4", "p5"]
    NUM_CLASSES: 5
  ROI_BOX_HEAD:
    NAME: "FastRCNNConvFCHead"
    NUM_FC: 2
    POOLER_RESOLUTION: 7
DATASETS:
  TRAIN: ("publaynet_train",)
  TEST: ("publaynet_val",)
SOLVER:
  IMS_PER_BATCH: 16
  BASE_LR: 0.02
INPUT:
  MIN_SIZE_TRAIN: (640, 672, 704, 736, 768, 800)
VERSION: 2
    """
    with open(LOCAL_CONFIG, "w") as f:
        f.write(config_content.strip())
    print("✅ Config file created.")

    # B. Download Weights (If missing)
    if not os.path.exists(LOCAL_WEIGHTS):
        print("⬇️  Downloading Weights (approx 330MB)...")
        # Use torch's robust downloader
        url = "https://www.dropbox.com/s/dgy9c10wykk4lq4/model_final.pth?dl=1"
        torch.hub.download_url_to_file(url, LOCAL_WEIGHTS)

    # C. Verify Load
    try:
        model = lp.Detectron2LayoutModel(
            config_path=LOCAL_CONFIG,
            model_path=LOCAL_WEIGHTS,
            label_map={0: "Text", 1: "Title",
                       2: "List", 3: "Table", 4: "Figure"},
            # Force CPU for LayoutParser on Mac
            extra_config=["MODEL.DEVICE", "cpu"]
        )
        print("✅ LayoutParser: READY (Loaded from local files)")
    except Exception as e:
        print(f"❌ LayoutParser Failed: {e}")

# --- 2. FLORENCE-2 SETUP (WITH PATCH) ---


def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
    """
    Filter out flash_attn from imports to prevent crash on Mac.
    """
    if not str(filename).endswith("modeling_florence2.py"):
        return get_imports(filename)
    imports = get_imports(filename)
    if "flash_attn" in imports:
        imports.remove("flash_attn")
    return imports


def setup_florence():
    print("\n--- 2. SETTING UP FLORENCE-2 ---")
    model_id = "microsoft/Florence-2-base"

    try:
        print(f"   Loading {model_id} using 'fixed_get_imports' patch...")

        # Apply the patch context
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            # Load Model
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True
            )
            # Load Processor
            processor = AutoProcessor.from_pretrained(
                model_id,
                trust_remote_code=True
            )

        print("✅ Florence-2: READY")
    except Exception as e:
        print(f"❌ Florence-2 Failed: {e}")


if __name__ == "__main__":
    setup_layoutparser()
    setup_florence()
