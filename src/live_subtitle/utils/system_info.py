import os
import torch
from src.live_subtitle.utils.logger import logger

def detect_hardware() -> dict:
    """
    Detects hardware capabilities for Faster-Whisper inference.
    Returns device ('cuda' or 'cpu'), compute_type, and hardware metadata.
    """
    has_cuda = torch.cuda.is_available()
    device = "cuda" if has_cuda else "cpu"
    compute_type = "float16" if has_cuda else "int8"
    device_name = "CPU"
    vram_gb = 0.0

    if has_cuda:
        try:
            device_name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            vram_gb = round(props.total_memory / (1024 ** 3), 2)
            logger.info(f"NVIDIA GPU detected: {device_name} ({vram_gb} GB VRAM). Using CUDA float16.")
        except Exception as e:
            logger.warning(f"Error querying CUDA properties: {e}")
    else:
        logger.info(f"CUDA not available. Using CPU int8 with {os.cpu_count() or 4} cores.")

    return {
        "has_cuda": has_cuda,
        "device": device,
        "compute_type": compute_type,
        "device_name": device_name,
        "vram_gb": vram_gb,
        "cpu_cores": os.cpu_count() or 4,
    }
