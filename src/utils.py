import torch
from transformers import AutoProcessor, AutoModelForCausalLM, AutoTokenizer
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer
from unittest.mock import patch
from transformers.dynamic_module_utils import get_imports


def fixed_get_imports(filename: str) -> list[str]:
    if not str(filename).endswith("modeling_florence2.py"):
        return get_imports(filename)
    imports = get_imports(filename)
    if "flash_attn" in imports:
        imports.remove("flash_attn")
    return imports


_florence_model = None
_florence_processor = None
_yolo_model = None
_sbert_model = None
_qwen_model = None
_qwen_tokenizer = None


def get_device():
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_florence_model():
    global _florence_model, _florence_processor
    if _florence_model is None:
        model_id = "microsoft/Florence-2-base"
        device = get_device()
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            _florence_processor = AutoProcessor.from_pretrained(
                model_id, trust_remote_code=True)
            _florence_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                attn_implementation="eager",
                trust_remote_code=True
            ).to(device)
    return _florence_model, _florence_processor


def load_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO('yolov8n.pt')
    return _yolo_model


def load_sbert_model():
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sbert_model


def get_slm():
    """Load Qwen2.5-1.5B for structured extraction."""
    global _qwen_model, _qwen_tokenizer
    if _qwen_model is None:
        model_id = "Qwen/Qwen2.5-1.5B-Instruct"
        _qwen_tokenizer = AutoTokenizer.from_pretrained(model_id)
        dtype = torch.bfloat16 if torch.cuda.is_available(
        ) and torch.cuda.get_device_capability()[0] >= 8 else "auto"
        _qwen_model = AutoModelForCausalLM.from_pretrained(
            model_id, dtype=dtype).to(get_device())
    return _qwen_model, _qwen_tokenizer
