import torch
import torch.nn as nn
from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
from pathlib import Path
from typing import Optional
import config
from utils import get_logger

logger = get_logger(__name__)

def prepare_model(backbone_model: str = "mbv3", num_classes: int = 2) -> nn.Module:
    """
    Prepare DeepLabV3 model with specified backbone
    
    Args:
        backbone_model: Backbone model type ('mbv3')
        num_classes: Number of output classes (2 for document segmentation)
    
    Returns:
        DeepLabV3 model
    """
    logger.info(f"Initializing DeepLabV3 with {backbone_model} backbone")
    
    if backbone_model == "mbv3":
        # Initialize model with default architecture (includes aux_classifier)
        model = deeplabv3_mobilenet_v3_large(weights=None, aux_loss=False)
    else:
        raise ValueError(f"Unsupported backbone: {backbone_model}")
    
    # Update the number of output channels for the output layer
    model.classifier[4] = nn.Conv2d(256, num_classes, kernel_size=1)
    
    return model

def load_model(
    model_name: str = config.DEFAULT_MODEL,
    device: Optional[str] = None
) -> tuple[nn.Module, str]:
    """
    Load the trained document segmentation model
    
    Args:
        model_name: Name of the model to load (from config.MODELS)
        device: Device to load model on ('cuda' or 'cpu')
    
    Returns:
        Tuple of (model, device_name)
    """
    if model_name not in config.MODELS:
        raise ValueError(f"Unknown model: {model_name}")
        
    model_config = config.MODELS[model_name]
    model_path = model_config['path']
    backbone = model_config['backbone']
    
    if device is None:
        device = config.DEVICE_PREFERENCE
    
    # Check if CUDA is available
    if device == 'cuda' and not torch.cuda.is_available():
        logger.warning("CUDA requested but not available, falling back to CPU")
        device = 'cpu'
    
    logger.info(f"Loading model: {model_name}")
    logger.info(f"Path: {model_path}")
    logger.info(f"Using device: {device}")
    
    # Initialize model architecture
    model = prepare_model(
        backbone_model=backbone,
        num_classes=config.MODEL_COMMON_CONFIG['num_classes']
    )
    
    # Load trained weights
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    try:
        state_dict = torch.load(model_path, map_location=device, weights_only=False)
        
        # Check for aux_classifier mismatch and handle it
        model_state = model.state_dict()
        
        # Filter out mismatched keys
        filtered_state_dict = {}
        for key, value in state_dict.items():
            if key in model_state:
                if model_state[key].shape == value.shape:
                    filtered_state_dict[key] = value
                else:
                    logger.warning(f"Skipping {key}: shape mismatch ({value.shape} vs {model_state[key].shape})")
            else:
                logger.warning(f"Skipping {key}: not in model")
        
        # Load the filtered state dict
        model.load_state_dict(filtered_state_dict, strict=False)
        logger.info("Model weights loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model weights: {e}")
        raise
    
    # Move model to device and set to evaluation mode
    model = model.to(device)
    model.eval()
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    return model, device

def get_model_info(model: nn.Module, model_name: str = "Unknown") -> dict:
    """
    Get information about the model
    
    Args:
        model: PyTorch model
        model_name: Name of the model
    
    Returns:
        Dictionary with model information
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    return {
        'total_params': total_params,
        'trainable_params': trainable_params,
        'architecture': f"DeepLabV3-{model_name}",
        'input_size': config.MODEL_COMMON_CONFIG['input_size'],
        'num_classes': config.MODEL_COMMON_CONFIG['num_classes'],
    }
