import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from unittest.mock import patch
from transformers.dynamic_module_utils import get_imports

# --- MAC SILICON PATCH FOR FLORENCE-2 ---


def fixed_get_imports(filename: str) -> list[str]:
    """
    Prevents flash_attn crash on Mac by filtering it out from imports.
    """
    if not str(filename).endswith("modeling_florence2.py"):
        return get_imports(filename)
    imports = get_imports(filename)
    if "flash_attn" in imports:
        imports.remove("flash_attn")
    return imports


# Global Cache (Lazy Loading)
_vision_model = None
_vision_processor = None


def load_vision_model():
    global _vision_model, _vision_processor

    if _vision_model is None:
        print("️ Loading Florence-2 Vision Model...")
        model_id = "microsoft/Florence-2-base"

        # Apply the patch while loading
        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            _vision_processor = AutoProcessor.from_pretrained(
                model_id, trust_remote_code=True)

            # Load with 'eager' attention for Mac support (Critical!)
            _vision_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                trust_remote_code=True,
                attn_implementation="eager"
            )

            # Move to GPU (MPS) if available
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            _vision_model.to(device)
            print(f"    Model loaded on {device}")

    return _vision_model, _vision_processor


def describe_image(image_np):
    """
    Takes a numpy image (crop of a diagram), runs Florence-2,
    returns a detailed text description.
    """
    model, processor = load_vision_model()
    device = model.device

    # Convert Numpy (OpenCV) to PIL
    # Handle Grayscale vs RGB inputs safely
    if len(image_np.shape) == 2:
        pil_image = Image.fromarray(image_np).convert("RGB")
    elif len(image_np.shape) == 3:
        pil_image = Image.fromarray(image_np)
    else:
        return "[Error: Invalid Image Shape]"

    # Prompt: We use detailed caption to get text + visual elements
    task_prompt = "<MORE_DETAILED_CAPTION>"

    inputs = processor(text=task_prompt, images=pil_image,
                       return_tensors="pt").to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False
        )

    generated_text = processor.batch_decode(
        generated_ids, skip_special_tokens=False)[0]

    # Post-process response to get just the caption
    parsed_answer = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(pil_image.width, pil_image.height)
    )

    return parsed_answer[task_prompt]
