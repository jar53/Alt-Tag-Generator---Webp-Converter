import os
import re
import logging
from PIL import Image, ImageFile
from iptcinfo3 import IPTCInfo
from image_captioner import generate_caption  # Ensure generate_caption is available and functional

# Allow truncated images to load without errors
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define input and output folders
input_folder = "input_folder"  # Replace with your actual path
output_folder = "output_folder"  # Replace with your actual path

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

def improve_caption(caption):
    """
    Refines the generated caption to make it more descriptive, avoids redundancy, and removes repeated words.
    """
    caption = re.sub(r'\b(A picture of|An image of|A photo of|A snapshot of)\b', '', caption, flags=re.IGNORECASE)
    caption = re.sub(r'(\b\w+\b)(?=.*\1)', '', caption)  # Remove repeated words
    caption = caption.strip()[:100].title()  # Limit to 100 chars for SEO
    logging.info(f"Caption improved: {caption}")
    return caption

def convert_to_jpeg(image_path):
    """Converts an image to JPEG format, if needed."""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")  # Convert to RGB for JPEG compatibility
            jpeg_path = os.path.splitext(image_path)[0] + ".jpg"
            img.save(jpeg_path, "JPEG")
            logging.info(f"Image converted to JPEG: {jpeg_path}")
            return jpeg_path
    except Exception as e:
        logging.error(f"Error converting {image_path} to JPEG: {e}")
        return None

def embed_iptc_metadata(image_path, title, description):
    """
    Embeds IPTC metadata for title, description, and keywords into the image without creating a backup.
    """
    try:
        temp_path = image_path + ".temp"
        
        # Load IPTC info with forced write mode
        info = IPTCInfo(image_path, force=True)
        
        # Set IPTC metadata fields
        info['object name'] = title  # Set Title
        info['caption/abstract'] = description  # Set Description
        info['keywords'] = [title]  # Add keywords
        
        # Save to a temporary file to avoid backup file creation
        info.save_as(temp_path)
        
        # Replace the original file with the temporary file
        os.replace(temp_path, image_path)
        
        logging.info(f"IPTC metadata embedded into {image_path}")
        
    except Exception as e:
        logging.error(f"Error embedding IPTC metadata into {image_path}: {e}")

def remove_processed_files(image_path):
    """
    Removes the original file from the input folder after successful processing.
    Only removes files that were converted or processed correctly.
    """
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logging.info(f"Removed original file: {image_path}")
    except Exception as e:
        logging.error(f"Error removing original file {image_path}: {e}")

def process_images():
    """
    Process images by converting to JPEG, generating captions, and embedding metadata.
    """
    # Remove any existing backup files before starting processing
    remove_backup_files()

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_folder, filename)

            # Convert to JPEG if needed
            if filename.lower().endswith('.png'):
                image_path = convert_to_jpeg(image_path)
                if not image_path:
                    continue  # Skip file if conversion failed

            # Generate a caption for the image
            caption = generate_caption(image_path)  
            if caption:
                improved_caption = improve_caption(caption)  # Improve the caption for SEO
                
                # Save the image with a descriptive filename in the output folder
                new_filename = improved_caption.replace(" ", "_")[:50] + ".jpg"
                new_file_path = os.path.join(output_folder, new_filename)

                # If the image file already exists, remove it first before saving the new one
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                    logging.info(f"Removed existing file with the same name: {new_file_path}")

                # Save the new file
                Image.open(image_path).convert("RGB").save(new_file_path)
                logging.info(f"Saved image to: {new_file_path}")
                
                # Embed IPTC metadata into the new image in the output folder
                embed_iptc_metadata(new_file_path, improved_caption, improved_caption)
                
                # Remove the original file from the input folder after processing
                remove_processed_files(image_path)

                logging.info(f"Processed and saved {new_file_path}")

def remove_backup_files():
    """
    Removes any backup files (e.g., files with a ~ suffix) from the output folder.
    """
    for filename in os.listdir(output_folder):
        if filename.endswith("~"):
            file_path = os.path.join(output_folder, filename)
            try:
                os.remove(file_path)
                logging.info(f"Removed backup file: {file_path}")
            except Exception as e:
                logging.error(f"Error removing backup file {file_path}: {e}")

if __name__ == "__main__":
    process_images()
