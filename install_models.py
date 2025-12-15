import os
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer


def install():
    model_id = "Qwen/Qwen2.5-1.5B-Instruct"
    AutoTokenizer.from_pretrained(model_id)
    AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")

    vision_id = "microsoft/Florence-2-base"
    AutoProcessor.from_pretrained(vision_id, trust_remote_code=True)
    AutoModelForCausalLM.from_pretrained(vision_id, trust_remote_code=True)

    SentenceTransformer('all-MiniLM-L6-v2')
    YOLO('yolov8n.pt')


if __name__ == "__main__":
    install()
