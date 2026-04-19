import pyautogui
import pytesseract
from PIL import Image
import os

# If Tesseract is not in your PATH, uncomment the line below and point it to your tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def take_screenshot(filename="screenshot.png"):
    """
    Takes a screenshot of the entire screen and saves it to a file.
    """
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"Screenshot saved successfully as {filename}")
        return filename
    except Exception as e:
        print(f"An error occurred while taking the screenshot: {e}")
        return None

def perform_ocr(image_path="screenshot.png"):
    """
    Performs OCR on the given image and returns the extracted text.
    """
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return None

if __name__ == "__main__":
    screenshot_file = take_screenshot()
    if screenshot_file:
        print("Performing OCR...")
        extracted_text = perform_ocr(screenshot_file)
        if extracted_text:
            print("\n--- Extracted Text ---\n")
            print(extracted_text)
            print("\n----------------------")
        else:
            print("No text could be extracted.")
