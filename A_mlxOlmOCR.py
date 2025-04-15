"""
Example Usages:

1. Processing PDF Files (using a list of PDFs):
   python A_mlxOlmOCR.py --pdfs /path/to/file1.pdf /path/to/file2.pdf --output-dir ./outputs

2. Processing a PDF Folder:
   python A_mlxOlmOCR.py --pdf-folder /path/to/pdf_folder --output-dir ./outputs

3. Processing an Image Folder:
   python A_mlxOlmOCR.py --image-folder /path/to/image_folder --output-dir ./outputs

4. Processing a Single Image:
   python A_mlxOlmOCR.py --image-file /path/to/your/image.png --output-dir ./outputs

5. Processing Multiple Image Files (merged into one output):
   python A_mlxOlmOCR.py --image-files /path/to/image1.png /path/to/image2.png --merge --output-dir ./outputs

6. Processing Multiple Image Files (separate outputs):
   python A_mlxOlmOCR.py --image-files /path/to/image1.png /path/to/image2.png --output-dir ./outputs

7. Using Clean Text Output:
   python A_mlxOlmOCR.py --image-file /path/to/your/image.png --clean_txt --output-dir ./outputs

Notes:
- Use the --help flag to display this usage information and additional details.
"""
import os
import sys
import glob
import argparse
import subprocess
import tempfile
import json  # Added for JSON parsing in --clean_txt feature

from pdf2image import convert_from_path
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Disable the decompression bomb protection (adjust as needed)

def process_image_file(image_path, model, max_tokens, temp_val, prompt, resize_shape, clean=False):
    """
    Process a single image file with the OCR model by calling the command-line tool.
    Returns the extracted text output.
    """
    cmd = [
        "python", "-m", "mlx_vlm.generate",
        "--model", model,
        "--max-tokens", str(max_tokens),
        "--temp", str(temp_val),
        "--prompt", prompt,
        "--image", image_path,
        "--resize-shape", str(resize_shape)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if clean:
            try:
                output_dict = json.loads(result.stdout)
                cleaned_text = output_dict.get("natural_text", result.stdout)
                return cleaned_text
            except json.JSONDecodeError:
                return result.stdout
        else:
            return result.stdout
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"\nError processing image {image_path}:\n{e.stderr}\n")
        return ""

def process_pdf(pdf_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean=False):
    """
    Convert a PDF into images (one per page) and process each image.
    The outputs are concatenated and saved to a text file whose name is the PDF's base name.
    """
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, base_name + ".txt")
    print(f"\nProcessing PDF: {pdf_path}")
    
    # Convert PDF pages to images (using 300 dpi for clarity)
    try:
        pages = convert_from_path(pdf_path, dpi=200)
    except Exception as e:
        sys.stderr.write(f"\nFailed to convert {pdf_path} to images: {e}\n")
        return

    combined_text = ""
    # Use a temporary directory to store the page images
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, page in enumerate(pages):
            temp_image_path = os.path.join(temp_dir, f"page_{i+1}.jpeg")
            page.save(temp_image_path, "JPEG")
            print(f"  Processing page {i+1}...")
            page_text = process_image_file(temp_image_path, model, max_tokens, temp_val, prompt, resize_shape, clean)
            combined_text += f"--- Page {i+1} ---\n" + page_text + "\n"
    
    # Save the combined text output to a file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_text)
    print(f"Output saved to: {output_file}")

def process_image_folder(folder_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean=False):
    """
    Process all image files in a folder in alphabetical order and combine the OCR outputs
    into a single text file named after the folder.
    """
    folder_name = os.path.basename(os.path.normpath(folder_path))
    output_file = os.path.join(output_dir, folder_name + ".txt")
    
    # Consider common image extensions
    image_extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff')
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
    image_files.sort()

    if not image_files:
        print(f"No image files found in folder: {folder_path}")
        return

    combined_text = ""
    for image_path in image_files:
        print(f"Processing image: {os.path.basename(image_path)}")
        file_text = process_image_file(image_path, model, max_tokens, temp_val, prompt, resize_shape, clean)
        combined_text += f"--- File: {os.path.basename(image_path)} ---\n" + file_text + "\n"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined_text)
    print(f"Output saved to: {output_file}")

def process_pdf_folder(folder_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean=False):
    """
    Process all PDF files in a given folder individually.
    Each PDF is processed by converting its pages to images and saving the results in a separate text file.
    """
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in folder: {folder_path}")
        return
    for pdf_path in sorted(pdf_files):
        print(f"Processing PDF: {pdf_path}")
        process_pdf(pdf_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean)

def process_single_image(image_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean=False):
    """
    Process a single image file with the OCR model and save the output to a text file named after the image.
    """
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_file = os.path.join(output_dir, base_name + ".txt")
    print(f"\nProcessing Image: {image_path}")

    text_output = process_image_file(image_path, model, max_tokens, temp_val, prompt, resize_shape, clean)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text_output)
    print(f"Output saved to: {output_file}")

def process_multiple_images(image_paths, model, max_tokens, temp_val, prompt, resize_shape, output_dir, merge=False, clean=False):
    """
    Process a list of image files. If merge is True, combine the outputs into a single text file.
    Otherwise, process each image individually and save separate text files.
    """
    if merge:
        combined_text = ""
        for image_path in image_paths:
            text_out = process_image_file(image_path, model, max_tokens, temp_val, prompt, resize_shape, clean)
            combined_text += f"--- File: {os.path.basename(image_path)} ---\n" + text_out + "\n"
        base_name = os.path.splitext(os.path.basename(image_paths[0]))[0]
        output_file = os.path.join(output_dir, base_name + ".txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(combined_text)
        print(f"Output saved to: {output_file}")
    else:
        for image_path in image_paths:
            process_single_image(image_path, model, max_tokens, temp_val, prompt, resize_shape, output_dir, clean)

def main():
    parser = argparse.ArgumentParser(
        description="Process PDF files or image folders with the mlx-community OCR model and aggregate outputs into a single text file.",
        epilog="""Examples:

Processing PDF Files:
    python A_mlxOlmOCR.py --pdfs /path/to/file1.pdf /path/to/file2.pdf --output-dir ./outputs

Processing a PDF Folder:
    python A_mlxOlmOCR.py --pdf-folder /path/to/pdf_folder --output-dir ./outputs

Processing an Image Folder:
    python A_mlxOlmOCR.py --image-folder /path/to/image_folder --output-dir ./outputs

Processing a Single Image:
    python A_mlxOlmOCR.py --image-file /path/to/your/image.png --output-dir ./outputs

Processing Multiple Image Files (merged):
    python A_mlxOlmOCR.py --image-files /path/to/image1.png /path/to/image2.png --merge --output-dir ./outputs

Processing Multiple Image Files (separate):
    python A_mlxOlmOCR.py --image-files /path/to/image1.png /path/to/image2.png --output-dir ./outputs

Using Clean Text Output:
    python A_mlxOlmOCR.py --image-file /path/to/your/image.png --clean_txt --output-dir ./outputs
"""
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdfs", nargs="+", help="List of PDF file paths to process.")
    group.add_argument("--pdf-folder", help="Path to a folder containing PDF files to process individually.")
    group.add_argument("--image-folder", help="Path to a folder containing images to process.")
    group.add_argument("--image-file", help="Path to a single image file to process.")
    group.add_argument("--image-files", nargs="+", help="List of image file paths to process. Use the --merge flag to combine outputs into a single file.")
    
    parser.add_argument("--model", default="mlx-community/olmOCR-7B-0225-preview-4bit", help="The model to use.")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Maximum tokens to generate for each image.")
    parser.add_argument("--temp", type=float, default=0.1, help="Temperature setting for generation.")
    parser.add_argument("--prompt", default="Describe this image.", help="Prompt to pass to the model.")
    parser.add_argument("--resize-shape", type=int, default=1024, help="Resize images so that the longest dimension equals this value.")
    parser.add_argument("--output-dir", default=".", help="Directory to save the output text files.")
    parser.add_argument("--merge", action="store_true", help="If processing multiple image files with --image-files, merge outputs into one text file. Otherwise, create separate files.")
    parser.add_argument("--clean_txt", action="store_true", help="If set, output text files will contain only the actual model outputs (cleaned), extracted from the JSON response.")
    args = parser.parse_args()

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    if args.pdfs:
        for pdf_path in args.pdfs:
            if os.path.isfile(pdf_path) and pdf_path.lower().endswith(".pdf"):
                process_pdf(pdf_path, args.model, args.max_tokens, args.temp, args.prompt, args.resize_shape, args.output_dir, clean=args.clean_txt)
            else:
                print(f"Skipping non-PDF file: {pdf_path}")
    elif args.pdf_folder:
        if os.path.isdir(args.pdf_folder):
            process_pdf_folder(args.pdf_folder, args.model, args.max_tokens, args.temp, args.prompt, args.resize_shape, args.output_dir, clean=args.clean_txt)
        else:
            print(f"Provided PDF folder is not a directory: {args.pdf_folder}")
    elif args.image_folder:
        if os.path.isdir(args.image_folder):
            process_image_folder(args.image_folder, args.model, args.max_tokens, args.temp, args.prompt, args.resize_shape, args.output_dir, clean=args.clean_txt)
        else:
            print(f"Provided image folder is not a directory: {args.image_folder}")
    elif args.image_file:
        if os.path.isfile(args.image_file):
            process_single_image(args.image_file, args.model, args.max_tokens, args.temp, args.prompt, args.resize_shape, args.output_dir, clean=args.clean_txt)
        else:
            print(f"Provided image file does not exist: {args.image_file}")
    elif args.image_files:
        process_multiple_images(args.image_files, args.model, args.max_tokens, args.temp, args.prompt, args.resize_shape, args.output_dir, merge=args.merge, clean=args.clean_txt)

if __name__ == "__main__":
    main()