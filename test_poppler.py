from pdf2image import convert_from_path
import os

# --- IMPORTANT: Change this to the exact path of your PDF file ---
PDF_FILE_PATH = "data/temp/IOT.pdf"

# --- For macOS with Homebrew, the path is almost always here ---
# For Apple Silicon (M1/M2/M3):
POPPLER_PATH_MAC_ARM = "/opt/homebrew/bin"
# For Intel Macs:
POPPLER_PATH_MAC_INTEL = "/usr/local/bin"


def run_test():
    print(f"--- Testing PDF conversion for: {PDF_FILE_PATH} ---")
    if not os.path.exists(PDF_FILE_PATH):
        print("!!! ERROR: PDF file not found at the specified path. Please check the path. !!!")
        return

    # --- Test 1: Let pdf2image try to find poppler on its own ---
    print("\n--- Running Test 1: Automatic Path Detection ---")
    try:
        images_auto = convert_from_path(PDF_FILE_PATH)
        print(f"Success! Images converted automatically: {len(images_auto)}")
        if len(images_auto) == 0:
            print(
                "Warning: Conversion returned an empty list. The PDF might be the issue.")
    except Exception as e:
        print(f"!!! FAILED: Automatic detection failed with an error. This is likely a PATH issue.")
        print(f"Error Details: {e}")

    # --- Test 2: Manually provide the poppler path ---
    print("\n--- Running Test 2: Manual Path Specification ---")
    try:
        # Try the Apple Silicon path first
        print(f"Attempting with poppler_path='{POPPLER_PATH_MAC_ARM}'...")
        images_manual = convert_from_path(
            PDF_FILE_PATH, poppler_path=POPPLER_PATH_MAC_ARM)
        print(
            f"Success! Images converted with manual path: {len(images_manual)}")
    except Exception as e:
        print(f"!!! FAILED: Manual path for Apple Silicon failed.")
        print(f"Error Details: {e}")
        try:
            # Fallback for Intel Macs
            print(
                f"\nAttempting with poppler_path='{POPPLER_PATH_MAC_INTEL}'...")
            images_manual_intel = convert_from_path(
                PDF_FILE_PATH, poppler_path=POPPLER_PATH_MAC_INTEL)
            print(
                f"Success! Images converted with manual Intel path: {len(images_manual_intel)}")
        except Exception as e2:
            print(f"!!! FAILED: Manual path for Intel Macs also failed.")
            print(f"Error Details: {e2}")


if __name__ == "__main__":
    run_test()
