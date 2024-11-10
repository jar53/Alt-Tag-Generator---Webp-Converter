import logging
import re
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, ImageFile

# Allow truncated images to load without errors
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Configure logging for error tracking
logging.basicConfig(level=logging.INFO)

# Initialize the model and processor
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path):
    """
    Generates a refined caption for a given image file.
    """
    try:
        # Open and process the image
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt")
        
        # Generate the caption
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        # Handle empty or generic captions
        if not caption or caption.lower() in ["a photo", "an image", "a picture", "a snapshot"]:
            caption = "No description available"
        
        # Refine the caption
        caption = refine_caption(caption)
        
        return caption
    
    except Exception as e:
        logging.error(f"Error processing {image_path}: {e}")
        return None

def refine_caption(caption):
    """
    Refines the generated caption to make it more descriptive, avoid redundancy, and remove repeated words.
    """
    # Remove redundant phrases like "A picture of", "An image of", etc.
    caption = re.sub(r'\b(A picture of|An image of|A photo of|A snapshot of)\b', '', caption, flags=re.IGNORECASE)
    
    # Remove repeated words (e.g., "operation_operation_operation_")
    caption = re.sub(r'(\b\w+\b)(?=.*\1)', '', caption)

    # Truncate long captions to a reasonable length for SEO (100 characters or so)
    caption = caption.strip()[:100]
    
    # Capitalize the first letter of each word for better readability
    caption = caption.title()
    
    return caption
