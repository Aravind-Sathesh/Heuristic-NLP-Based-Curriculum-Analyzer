import os

# Get the absolute path of the project root
# (Assumes this file is in src/utils.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Model Paths
MODEL_DIR = os.path.join(BASE_DIR, "src", "models", "layoutparser")
LP_CONFIG_PATH = os.path.join(MODEL_DIR, "config.yml")
LP_WEIGHTS_PATH = os.path.join(MODEL_DIR, "model_final.pth")


def validate_paths():
    """Ensures model files exist before execution."""
    if not os.path.exists(LP_CONFIG_PATH) or not os.path.exists(LP_WEIGHTS_PATH):
        raise FileNotFoundError(
            f"Model files missing in {MODEL_DIR}. Please run 'python install_models.py' first."
        )
