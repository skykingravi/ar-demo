import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import requests
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add the origin of your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Path to Tesseract executable (set it to your installation path)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Update with your Tesseract path

# Preprocess the image for better OCR accuracy
def preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert('L')  # Grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Increase contrast
    image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
    return image

# Extract dish names and prices from image using OCR
def extract_text_from_image(image: Image.Image) -> dict:
    ocr_text = pytesseract.image_to_string(image, lang='mal')
    print(ocr_text)
    menu_items = {}
    lines = ocr_text.splitlines()

    for line in lines:
        # Use regex to match lines with dish names followed by a price at the end
        match = re.match(r"(.+?)\s+(\d+)$", line)  # Only lines ending with a price
        if match:
            dish_name = match.group(1).strip()
            price = match.group(2).strip()
            menu_items[dish_name] = price
    print(menu_items)
    return menu_items

# Translate Malayalam text to English using unofficial Google Translate API
def translate_to_english(text: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "ml",
        "tl": "en",
        "dt": "t",
        "q": text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        translated_text = response.json()[0][0][0]
        return translated_text
    else:
        return "Translation failed."

# Translate all dish names in the menu dictionary
def translate_menu(menu_items: dict) -> dict:
    translated_menu = {}
    for dish_name, price in menu_items.items():
        translated_dish_name = translate_to_english(dish_name)
        translated_menu[translated_dish_name] = price
    return translated_menu

# FastAPI endpoint to upload image and get translated menu
@app.post("/upload-menu/")
async def upload_menu(file: UploadFile = File(...)):
    try:
        print({"filename": file.filename, "size": len(await file.read())})
        save_path = f"temp/{file.filename}"

        # Save the image file locally
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Open the image file
        image = Image.open(file.file)
        preprocessed_image = preprocess_image(image)
        
        # Extract text and translate
        menu_items = extract_text_from_image(preprocessed_image)
        translated_menu = translate_menu(menu_items)
        
        # Return JSON response
        return JSONResponse(content={"menu": translated_menu})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))