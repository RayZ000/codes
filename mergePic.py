import os
import sys
from PIL import Image

def create_composite(images, output_filename):
    """
    Combine four images (assumed to be the same size) into a 2x2 grid and save the composite.
    """
    # Use the size of the first image for width and height
    w, h = images[0].size
    composite = Image.new('RGB', (w * 2, h * 2), color=(255, 255, 255))
    
    # Paste images into a 2x2 grid
    composite.paste(images[0], (0, 0))
    composite.paste(images[1], (w, 0))
    composite.paste(images[2], (0, h))
    composite.paste(images[3], (w, h))
    
    composite.save(output_filename)
    print(f"Saved composite image: {output_filename}")

def main(folder):
    # Define valid image extensions
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    
    # Get sorted list of image file names in the folder
    files = sorted([
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in valid_extensions
    ])
    
    if not files:
        print("No image files found in the folder.")
        return
    
    # Group files into batches of 4
    groups = [files[i:i+4] for i in range(0, len(files), 4)]
    
    for i, group in enumerate(groups):
        images = []
        for filename in group:
            try:
                img_path = os.path.join(folder, filename)
                img = Image.open(img_path)
                images.append(img)
            except Exception as e:
                print(f"Error opening {filename}: {e}")
        
        # If there are fewer than 4 images in the group, add white images
        if len(images) < 4:
            # Use dimensions of the first image in the group or default to 200x200 if group is empty
            if images:
                w, h = images[0].size
            else:
                w, h = (200, 200)
            # Append white images until we have 4 images
            while len(images) < 4:
                white_img = Image.new('RGB', (w, h), color=(255, 255, 255))
                images.append(white_img)
        
        # Create composite image for the group
        output_filename = os.path.join(folder, f'composite_{i+1}.jpg')
        create_composite(images, output_filename)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print("The provided folder path does not exist or is not a directory.")
        sys.exit(1)
    
    main(folder_path)