import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io
import os
import base64
import glob
import re
import urllib.parse
import urllib.request
import json
import textwrap
import io
from xhtml2pdf import pisa
import random
import sqlite3
import concurrent.futures
from gtts import gTTS

def download_image(image_url):
    try:
        req = urllib.request.Request(
            image_url, 
            data=None, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            return response.read()
    except:
        return None

def generate_pdf_parallel(standalone_html):
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(standalone_html), dest=pdf_buffer)
    if not pisa_status.err:
        return pdf_buffer.getvalue()
    return None

def text_to_audio(text, lang_code):
    try:
        # Extract base language code (e.g., 'en-IN' -> 'en')
        base_lang = lang_code.split('-')[0]
        
        # Split text into sentences for parallel processing
        import re
        # Splitting by common sentence terminators
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        
        if not sentences:
            return None
            
        results = [None] * len(sentences)
        
        def fetch_chunk(i, s):
            try:
                tts = gTTS(text=s, lang=base_lang)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                results[i] = fp.getvalue()
            except:
                results[i] = b""
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for i, s in enumerate(sentences):
                executor.submit(fetch_chunk, i, s)
                
        return b"".join([r for r in results if r])
    except Exception as e:
        return None

THEMES = [
    {
        "name": "Classic Culinary",
        "bg_gradient": "linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%)",
        "text_color": "#333333",
        "title_color": "#e63946",
        "title_border": "#e63946",
        "desc_color": "#555555",
        "meta_bg": "#f1faee",
        "meta_text": "#1d3557",
        "heading_color": "#457b9d",
        "heading_border": "#a8dadc",
        "tip_bg": "#fff3cd",
        "tip_border": "#ffeeba",
        "tip_text": "#856404"
    },
    {
        "name": "Earthy Rustic",
        "bg_gradient": "linear-gradient(135deg, #fff9f2 0%, #f4e8d8 100%)",
        "text_color": "#4a3b32",
        "title_color": "#d95c14",
        "title_border": "#d95c14",
        "desc_color": "#6e5d53",
        "meta_bg": "#e9dec9",
        "meta_text": "#4a3b32",
        "heading_color": "#5c6b45",
        "heading_border": "#8a9a6b",
        "tip_bg": "#f9f2e3",
        "tip_border": "#e6d5b8",
        "tip_text": "#7a5c33"
    },
    {
        "name": "Fresh Mint",
        "bg_gradient": "linear-gradient(135deg, #ffffff 0%, #e8f9f2 100%)",
        "text_color": "#2c3e38",
        "title_color": "#118a6a",
        "title_border": "#118a6a",
        "desc_color": "#4d6b61",
        "meta_bg": "#d0f2e6",
        "meta_text": "#1b4d3e",
        "heading_color": "#1b4d3e",
        "heading_border": "#85d1b5",
        "tip_bg": "#e6faf2",
        "tip_border": "#b8e6d2",
        "tip_text": "#165942"
    },
    {
        "name": "Midnight Elegance",
        "bg_gradient": "linear-gradient(135deg, #2b2b2b 0%, #1a1a1a 100%)",
        "text_color": "#e0e0e0",
        "title_color": "#d4af37",
        "title_border": "#d4af37",
        "desc_color": "#aaaaaa",
        "meta_bg": "#333333",
        "meta_text": "#f5f5f5",
        "heading_color": "#c4a331",
        "heading_border": "#555555",
        "tip_bg": "#423d26",
        "tip_border": "#6b5e28",
        "tip_text": "#e0cc8d"
    },
    {
        "name": "Vibrant Citrus",
        "bg_gradient": "linear-gradient(135deg, #fffdf2 0%, #fff4cc 100%)",
        "text_color": "#4d4133",
        "title_color": "#d62828",
        "title_border": "#d62828",
        "desc_color": "#6b5a47",
        "meta_bg": "#ffe6a3",
        "meta_text": "#993d00",
        "heading_color": "#e67300",
        "heading_border": "#ffb84d",
        "tip_bg": "#fff2cc",
        "tip_border": "#ffcc80",
        "tip_text": "#b35900"
    }
]

def render_recipe_card(recipe_data, image_url=None):
    theme = random.choice(THEMES)
    title = recipe_data.get("title", "Delicious Recipe")
    desc = recipe_data.get("description", "")
    prep = recipe_data.get("prep_time", "-")
    cook = recipe_data.get("cook_time", "-")
    servings = recipe_data.get("servings", "-")
    ingredients = recipe_data.get("ingredients", [])
    instructions = recipe_data.get("instructions", [])
    tip = recipe_data.get("tip", "")

    calories = recipe_data.get("calories", "-")
    protein = recipe_data.get("protein", "-")
    carbs = recipe_data.get("carbs", "-")
    fat = recipe_data.get("fat", "-")
    badges = recipe_data.get("badges", [])
    
    badge_html = ""
    for badge in badges:
        badge_html += f"<span style='background-color: {theme['title_color']}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8em; margin: 0 5px; display: inline-block;'>{badge}</span>"
    if badge_html:
        badge_html = f"<div style='text-align: center; margin-bottom: 15px;'>{badge_html}</div>"

    macro_html = f"""
        <div style="display: flex; justify-content: space-around; margin-bottom: 25px; text-align: center;">
            <div style="background: {theme['meta_bg']}; padding: 10px; border-radius: 10px; width: 22%;">
                <div style="font-size: 0.85em; color: {theme['meta_text']};">Calories</div>
                <div style="font-weight: bold; color: {theme['title_color']};">{calories}</div>
            </div>
            <div style="background: {theme['meta_bg']}; padding: 10px; border-radius: 10px; width: 22%;">
                <div style="font-size: 0.85em; color: {theme['meta_text']};">Protein</div>
                <div style="font-weight: bold; color: {theme['title_color']};">{protein}</div>
            </div>
            <div style="background: {theme['meta_bg']}; padding: 10px; border-radius: 10px; width: 22%;">
                <div style="font-size: 0.85em; color: {theme['meta_text']};">Carbs</div>
                <div style="font-weight: bold; color: {theme['title_color']};">{carbs}</div>
            </div>
            <div style="background: {theme['meta_bg']}; padding: 10px; border-radius: 10px; width: 22%;">
                <div style="font-size: 0.85em; color: {theme['meta_text']};">Fat</div>
                <div style="font-weight: bold; color: {theme['title_color']};">{fat}</div>
            </div>
        </div>
    """

    ing_html = "".join([f"<li>{item}</li>" for item in ingredients])
    inst_html = "".join([f"<li>{item}</li>" for item in instructions])

    img_html = f'<img src="{image_url}" alt="{title}" class="recipe-img">' if image_url else ""
    tip_html = f"<div class='chef-tip'><strong>💡 Chef's Tip:</strong> {tip}</div>" if tip else ""

    html_content = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: {theme['bg_gradient']}; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); overflow: hidden; margin-bottom: 20px; color: {theme['text_color']};">
    {img_html}
    <div style="padding: 30px;">
        <h2 style="color: {theme['title_color']}; text-align: center; font-size: 2.2em; margin-top: 0; margin-bottom: 10px; border-bottom: 2px solid {theme['title_border']}; padding-bottom: 15px;">🍽️ {title}</h2>
        {badge_html}
        <p style="text-align: center; font-style: italic; color: {theme['desc_color']}; font-size: 1.1em; margin-bottom: 25px;">{desc}</p>
        
        {macro_html}
        
        <div style="display: flex; justify-content: space-around; background-color: {theme['meta_bg']}; padding: 15px; border-radius: 12px; margin-bottom: 30px; font-weight: bold; color: {theme['meta_text']}; flex-wrap: wrap; gap: 10px;">
            <span style="display: flex; align-items: center; gap: 5px;">⏱️ <strong>Prep:</strong> {prep}</span>
            <span style="display: flex; align-items: center; gap: 5px;">🍳 <strong>Cook:</strong> {cook}</span>
            <span style="display: flex; align-items: center; gap: 5px;">👪 <strong>Servings:</strong> {servings}</span>
        </div>
        
        <h3 style="color: {theme['heading_color']}; border-bottom: 1px solid {theme['heading_border']}; padding-bottom: 5px;">🛒 Ingredients</h3>
        <ul style="line-height: 1.8; font-size: 1.05em; padding-left: 20px; margin-bottom: 25px;">
            {ing_html}
        </ul>
        
        <h3 style="color: {theme['heading_color']}; border-bottom: 1px solid {theme['heading_border']}; padding-bottom: 5px;">👨‍🍳 Instructions</h3>
        <ol style="line-height: 1.8; font-size: 1.05em; padding-left: 20px; margin-bottom: 30px;">
            {inst_html}
        </ol>
        
        {tip_html}
        <p style="text-align: center; margin-top: 30px; font-weight: bold; color: {theme['title_color']}; font-size: 1.2em;">🍽️ Have a delicious meal 🍽️</p>
    </div>
</div>
"""
    
    standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ background-color: #e5e5e5; padding: 20px; display: flex; justify-content: center; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .recipe-container {{ max-width: 800px; width: 100%; }}
        .recipe-img {{ width: 100%; height: 350px; object-fit: cover; border-bottom: 5px solid {theme['title_color']}; display: block; }}
        .chef-tip {{ background-color: {theme['tip_bg']}; color: {theme['tip_text']}; padding: 15px; border-left: 5px solid {theme['tip_border']}; border-radius: 5px; font-style: italic; }}
    </style>
</head>
<body>
    <div class="recipe-container">
        {html_content}
    </div>
</body>
</html>"""
    
    inline_html = f"""
<style>
    .recipe-img {{ width: 100%; height: 350px; object-fit: cover; border-bottom: 5px solid {theme['title_color']}; display: block; }}
    .chef-tip {{ background-color: {theme['tip_bg']}; color: {theme['tip_text']}; padding: 15px; border-left: 5px solid {theme['tip_border']}; border-radius: 5px; font-style: italic; }}
</style>
{html_content}
"""
    
    # Strip leading whitespace so Streamlit does not render HTML as markdown code blocks
    inline_html = "".join([line.lstrip() for line in inline_html.splitlines(True)])
    standalone_html = "".join([line.lstrip() for line in standalone_html.splitlines(True)])
    
    return inline_html, standalone_html

# Load environment variables
load_dotenv()

# Initialize session state keys for inputs
if "ingredients_input" not in st.session_state:
    st.session_state.ingredients_input = ""
if "cuisine_input" not in st.session_state:
    st.session_state.cuisine_input = ""
if "dietary_input" not in st.session_state:
    st.session_state.dietary_input = ""
if "recipe_name_input" not in st.session_state:
    st.session_state.recipe_name_input = ""
if "current_recipe" not in st.session_state:
    st.session_state.current_recipe = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "cooking_mode_active" not in st.session_state:
    st.session_state.cooking_mode_active = False
if "cooking_step_index" not in st.session_state:
    st.session_state.cooking_step_index = 0

def transcribe_audio(audio_bytes, lang_code):
    r = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language=lang_code)
            return text
    except sr.UnknownValueError:
        st.warning("Could not understand the audio. Please try speaking clearly.")
        return ""
    except sr.RequestError as e:
        st.error(f"Could not request results from Speech Recognition service; {e}")
        return ""
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return ""

COMMON_INGREDIENTS = [
    "Tomato 🍅", "Onion 🧅", "Garlic 🧄", "Potato 🥔", "Carrot 🥕", "Bell Pepper 🫑", "Spinach 🍃", "Broccoli 🥦", "Cauliflower 🥦", "Mushroom 🍄", "Chili Pepper 🌶️", "Corn 🌽",
    "Chicken 🍗", "Beef 🥩", "Pork 🥓", "Fish 🐟", "Shrimp 🍤", "Egg 🥚", "Tofu 🧈", "Lentils 🍲", "Chickpeas 🧆",
    "Pasta 🍝", "Rice 🍚", "Bread 🍞", "Noodles 🍜", "Quinoa 🌾",
    "Milk 🥛", "Cheese 🧀", "Butter 🧈", "Yogurt 🥣",
    "Soy Sauce 🫙", "Olive Oil 🫒", "Lemon 🍋", "Lime 🍋‍🟩", "Ginger 🫚", "Honey 🍯", "Basil 🌿", "Cilantro 🌿", "Parsley 🌿"
]

# UI Translations
TRANSLATIONS = {
    "English": {
        "title": "🍳 Recipe Craft AI",
        "subtitle": "Enter your available ingredients and preferred cuisine, and let AI craft a delicious recipe for you for free!",
        "settings": "⚙️ Settings",
        "language": "Language / भाषा",
        "api_key_label": "Gemini API Key",
        "api_key_help": "Enter your Google Gemini API Key. It is completely free!",
        "api_key_how": "### How to get a free API Key:\n1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).\n2. Sign in with any regular Google Account.\n3. Click the big blue **Create API Key** button.\n4. Copy it and paste it here! (It usually starts with `AIza...`)",
        "generator": "🛒 Recipe Generator",
        "search_mode": "Search Mode",
        "by_ingredients": "By Ingredients🥕",
        "by_recipe": "By Recipe Name 🍳",
        "by_image": "By Image 📸",
        "by_visual": "Visual Selection 🍱",
        "visual_help": "Select the ingredients you have from the grid below.",
        "upload_image": "Upload Image of Ingredients",
        "upload_image_help": "Upload a picture of your fridge or pantry items.",
        "warn_image": "Please upload an image!",
        "recipe_name": "Recipe Name",
        "recipe_name_ph": "e.g., Chicken Tikka Masala, Pasta Carbonara",
        "recipe_name_help": "Enter the specific recipe you want to make. You can also use the microphone!",
        "warn_recipe": "Please enter a recipe name!",
        "ingredients": "Ingredients",
        "ingredients_ph": "e.g., chicken breasts, garlic, tomatoes, onions",
        "ingredients_help": "List the ingredients you want to use. You can also use the microphone!",
        "cuisine": "Cuisine Preference",
        "cuisine_ph": "e.g., Italian, Mexican, Mediterranean",
        "cuisine_help": "Select or type your preferred cuisine. You can also use the microphone!",
        "dietary": "Dietary Preferences (Optional)",
        "dietary_ph": "e.g., Vegan, Gluten-Free, Keto",
        "dietary_help": "Any specific dietary restrictions? You can also use the microphone!",
        "meal_type": "Meal Type",
        "meal_type_options": ["Any", "Breakfast", "Lunch", "Dinner", "Snack", "Dessert"],
        "skill_level": "Skill Level",
        "skill_level_options": ["Beginner", "Intermediate", "Advanced"],
        "max_time": "Max Cooking Time (mins)",
        "button": "✨ Suggest Recipe",
        "button_create": "✨ Create Recipe",
        "error_api": "Please provide a free Google Gemini API Key in the sidebar.",
        "warn_ing": "Please enter some ingredients!",
        "warn_cui": "Please enter a cuisine preference!",
        "spinner": "Crafting your recipe using Craft AI... 🧑‍🍳",
        "success": "Bon Appétit! Here is your generated recipe:",
        "error_gen": "An error occurred while generating the recipe. Error details: ",
        "download": "⬇️ Download Recipe",
        "speak": "🎤 Speak",
        "stop": "⏹️ Stop",
        "transcribing": "Transcribing audio...",
        "speech_lang": "en-IN",
        "chat_title": "💬 Chef Chat",
        "chat_subtitle": "Got a question about this recipe? Need a substitution? Ask away!",
        "chat_placeholder": "E.g., What if I don't have a whisk?"
    },
    "Hindi": {
        "title": "🍳 रेसिपी क्राफ्ट एआई",
        "subtitle": "अपनी उपलब्ध सामग्री और पसंदीदा व्यंजन दर्ज करें, और AI को आपके लिए एक स्वादिष्ट रेसिपी तैयार करने दें!",
        "settings": "⚙️ सेटिंग्स",
        "language": "Language / भाषा",
        "api_key_label": "Gemini API Key",
        "api_key_help": "अपनी Google Gemini API Key दर्ज करें। यह बिल्कुल मुफ़्त है!",
        "api_key_how": "### मुफ्त API Key कैसे प्राप्त करें:\n1. [Google AI Studio](https://aistudio.google.com/app/apikey) पर जाएं।\n2. किसी भी Google खाते से साइन इन करें।\n3. **Create API Key** बटन पर क्लिक करें।\n4. इसे कॉपी करें और यहां पेस्ट करें!",
        "generator": "🛒 रेसिपी जेनरेटर",
        "search_mode": "खोज मोड (Search Mode)",
        "by_ingredients": "सामग्री के अनुसार (By Ingredients)🥕",
        "by_recipe": "रेसिपी के नाम से (By Recipe Name)🍳",
        "by_image": "चित्र द्वारा (By Image)📸",
        "by_visual": "दृश्य चयन (Visual Selection) 🍱",
        "visual_help": "नीचे दिए गए ग्रिड से आपके पास मौजूद सामग्री का चयन करें।",
        "upload_image": "सामग्री का चित्र अपलोड करें",
        "upload_image_help": "अपने फ्रिज या पैंट्री आइटम की तस्वीर अपलोड करें।",
        "warn_image": "कृपया एक चित्र अपलोड करें!",
        "recipe_name": "रेसिपी का नाम (Recipe Name)",
        "recipe_name_ph": "उदा. चिकन टिक्का मसाला, पास्ता",
        "recipe_name_help": "वह विशिष्ट रेसिपी दर्ज करें जिसे आप बनाना चाहते हैं। आप माइक का भी उपयोग कर सकते हैं!",
        "warn_recipe": "कृपया रेसिपी का नाम दर्ज करें!",
        "ingredients": "सामग्री (Ingredients)",
        "ingredients_ph": "उदा. चिकन, लहसुन, टमाटर, प्याज",
        "ingredients_help": "उन सामग्रियों की सूची बनाएं जिनका आप उपयोग करना चाहते हैं। आप माइक का भी उपयोग कर सकते हैं!",
        "cuisine": "पसंदीदा व्यंजन (Cuisine)",
        "cuisine_ph": "उदा. इटैलियन, मैक्सिकन, इंडियन",
        "cuisine_help": "अपना पसंदीदा व्यंजन चुनें या टाइप करें। आप माइक का भी उपयोग कर सकते हैं!",
        "dietary": "आहार प्राथमिकताएं (वैकल्पिक)",
        "dietary_ph": "उदा. शाकाहारी, ग्लूटेन-मुक्त",
        "dietary_help": "क्या कोई विशिष्ट आहार प्रतिबंध है? आप माइक का भी उपयोग कर सकते हैं!",
        "meal_type": "भोजन का प्रकार",
        "meal_type_options": ["कोई भी", "नाश्ता", "दोपहर का भोजन", "रात का भोजन", "स्नैक", "मिठाई"],
        "skill_level": "कौशल स्तर",
        "skill_level_options": ["शुरुआती", "मध्यम", "उन्नत"],
        "max_time": "अधिकतम पकाने का समय (मिनट)",
        "button": "✨ रेसिपी सुझाएं",
        "button_create": "✨ रेसिपी बनाएं",
        "error_api": "कृपया साइडबार में एक मुफ्त Google Gemini API Key प्रदान करें।",
        "warn_ing": "कृपया कुछ सामग्री दर्ज करें!",
        "warn_cui": "कृपया व्यंजन प्राथमिकता दर्ज करें!",
        "spinner": "क्राफ्ट एआई का उपयोग करके आपकी रेसिपी तैयार की जा रही है... 🧑‍🍳",
        "success": "बॉन अपेटिट! यहाँ आपकी तैयार रेसिपी है:",
        "error_gen": "रेसिपी बनाते समय एक त्रुटि हुई। त्रुटि विवरण: ",
        "download": "⬇️ रेसिपी डाउनलोड करें",
        "speak": "🎤 बोलें",
        "stop": "⏹️ रोकें",
        "transcribing": "ऑडियो ट्रांसक्राइब किया जा रहा है...",
        "speech_lang": "hi-IN",
        "chat_title": "💬 शेफ चैट",
        "chat_subtitle": "क्या इस रेसिपी के बारे में कोई सवाल है? कोई विकल्प चाहिए? बेझिझक पूछें!",
        "chat_placeholder": "उदा. अगर मेरे पास व्हिस्क नहीं है तो क्या करूँ?"
    },
    "Marathi": {
        "title": "🍳 रेसिपी क्राफ्ट एआय",
        "subtitle": "तुमचे उपलब्ध साहित्य आणि आवडता पदार्थ टाका आणि AI ला तुमच्यासाठी एक चविष्ट रेसिपी तयार करू द्या!",
        "settings": "⚙️ सेटिंग्ज",
        "language": "Language / भाषा",
        "api_key_label": "Gemini API Key",
        "api_key_help": "तुमची Google Gemini API Key टाका. हे पूर्णपणे मोफत आहे!",
        "api_key_how": "### मोफत API Key कशी मिळवावी:\n1. [Google AI Studio](https://aistudio.google.com/app/apikey) वर जा.\n2. कोणत्याही Google खात्याने साइन इन करा.\n3. **Create API Key** बटणावर क्लिक करा.\n4. कॉपी करा आणि येथे पेस्ट करा!",
        "generator": "🛒 रेसिपी जनरेटर",
        "search_mode": "शोध मोड (Search Mode)",
        "by_ingredients": "साहित्यानुसार (By Ingredients)🥕",
        "by_recipe": "रेसिपीच्या नावानुसार (By Recipe Name)🍳",
        "by_image": "चित्रानुसार (By Image)📸",
        "by_visual": "दृश्य निवड (Visual Selection) 🍱",
        "visual_help": "खालील ग्रिडमधून तुमच्याकडे असलेले साहित्य निवडा.",
        "upload_image": "साहित्याचे चित्र अपलोड करा",
        "upload_image_help": "तुमच्या फ्रीज किंवा पँट्रीमधील वस्तूंचा फोटो अपलोड करा.",
        "warn_image": "कृपया एक चित्र अपलोड करा!",
        "recipe_name": "रेसिपीचे नाव (Recipe Name)",
        "recipe_name_ph": "उदा. चिकन टिक्का मसाला, पास्ता",
        "recipe_name_help": "तुम्हाला बनवायची असलेली विशिष्ट रेसिपी टाका. तुम्ही माईक देखील वापरू शकता!",
        "warn_recipe": "कृपया रेसिपीचे नाव टाका!",
        "ingredients": "साहित्य (Ingredients)",
        "ingredients_ph": "उदा. चिकन, लसूण, टोमॅटो, कांदा",
        "ingredients_help": "तुम्हाला वापरायच्या असलेल्या साहित्याची यादी करा. तुम्ही माईक देखील वापरू शकता!",
        "cuisine": "आवडता पदार्थ (Cuisine)",
        "cuisine_ph": "उदा. इटालियन, मेक्सिकन, महाराष्ट्रीयन",
        "cuisine_help": "तुमचा आवडता पदार्थ निवडा किंवा टाइप करा. तुम्ही माईक देखील वापरू शकता!",
        "dietary": "आहाराची पसंती (पर्यायी)",
        "dietary_ph": "उदा. शाकाहारी, ग्लूटेन-फ्री",
        "dietary_help": "कोणतेही विशिष्ट आहाराचे निर्बंध? तुम्ही माईक देखील वापरू शकता!",
        "meal_type": "जेवणाचा प्रकार",
        "meal_type_options": ["कोणतेही", "न्याहारी", "दुपारचे जेवण", "रात्रीचे जेवण", "स्नॅक", "मिठाई"],
        "skill_level": "कौशल्य पातळी",
        "skill_level_options": ["सुरुवातीची", "मध्यम", "प्रगत"],
        "max_time": "कमाल शिजवण्याची वेळ (मिनिटे)",
        "button": "✨ रेसिपी सुचवा",
        "button_create": "✨ रेसिपी तयार करा",
        "error_api": "कृपया साइडबारमध्ये मोफत Google Gemini API Key द्या.",
        "warn_ing": "कृपया काही साहित्य टाका!",
        "warn_cui": "कृपया पदार्थाची पसंती टाका!",
        "spinner": "क्राफ्ट एआय वापरून तुमची रेसिपी तयार केली जात आहे... 🧑‍🍳",
        "success": "बॉन अॅपेटिट! तुमची तयार केलेली रेसिपी येथे आहे:",
        "error_gen": "रेसिपी तयार करताना एक त्रुटी आली. त्रुटी तपशील: ",
        "download": "⬇️ रेसिपी डाउनलोड करा",
        "speak": "🎤 बोला",
        "stop": "⏹️ थांबवा",
        "transcribing": "ऑडिओ ट्रान्सक्राइब होत आहे...",
        "speech_lang": "mr-IN",
        "chat_title": "💬 शेफ चॅट",
        "chat_subtitle": "या रेसिपीबद्दल काही प्रश्न आहे का? काही पर्याय हवा आहे का? नक्की विचारा!",
        "chat_placeholder": "उदा. माझ्याकडे व्हिस्क नसेल तर काय करावे?"
    }
}

st.set_page_config(page_title="Recipe Craft AI", page_icon="🍳", layout="centered")

def set_local_background():
    bg_files = glob.glob("bg.*")
    if bg_files:
        bg_file = bg_files[0]
        ext = bg_file.split('.')[-1]
        try:
            with open(bg_file, "rb") as f:
                data = f.read()
            bin_str = base64.b64encode(data).decode()
            page_bg_img = f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("data:image/{ext};base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            """
            st.markdown(page_bg_img, unsafe_allow_html=True)
        except Exception as e:
            pass

set_local_background()

# Sidebar for Setup
with st.sidebar:
    st.header("🗺️ Navigation")
    page = st.radio("", ["🍳 Generate Recipe", "📖 My Cookbook"], label_visibility="collapsed")
    st.markdown("---")
    
    selected_language = st.selectbox("Language / भाषा", ["English", "Hindi", "Marathi"])
    t = TRANSLATIONS[selected_language]
    current_speech_lang = t["speech_lang"]
    
    st.header(t["settings"])
    api_key_input = st.text_input(t["api_key_label"], type="password", help=t["api_key_help"])
    st.markdown("---")
    st.markdown(t["api_key_how"])
    
    # Prioritize user input over .env
    gemini_api_key = api_key_input or os.getenv("GOOGLE_API_KEY")

# Database initialization
def init_db():
    conn = sqlite3.connect("cookbook.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    cuisine TEXT,
                    image_url TEXT,
                    recipe_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def save_recipe(title, cuisine, image_url, recipe_json):
    conn = sqlite3.connect("cookbook.db")
    c = conn.cursor()
    c.execute("INSERT INTO recipes (title, cuisine, image_url, recipe_json) VALUES (?, ?, ?, ?)",
              (title, cuisine, image_url, recipe_json))
    conn.commit()
    conn.close()

def get_saved_recipes():
    conn = sqlite3.connect("cookbook.db")
    c = conn.cursor()
    c.execute("SELECT id, title, cuisine, image_url, recipe_json, created_at FROM recipes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

if page == "📖 My Cookbook":
    st.title("📖 My Cookbook")
    st.markdown("Welcome to your personal recipe collection! Here are all the amazing recipes you have saved.")
    
    saved_recipes = get_saved_recipes()
    if not saved_recipes:
        st.info("Your cookbook is empty! Go generate some recipes and click the ❤️ Save to Cookbook button.")
    else:
        for row in saved_recipes:
            db_id, db_title, db_cuisine, db_image_url, db_json_str, db_time = row
            try:
                recipe_data = json.loads(db_json_str)
            except:
                continue
            
            with st.expander(f"🍽️ {db_title} ({db_cuisine}) - Saved on {db_time.split()[0]}"):
                inline_html, _ = render_recipe_card(recipe_data, db_image_url)
                
                # Build regular markdown text for display
                md = f"### 🍽️ {db_title}\n\n"
                badges = recipe_data.get("badges", [])
                if badges:
                    md += "**Tags:** " + " ".join([f"`{b}`" for b in badges]) + "\n\n"
                md += f"*{recipe_data.get('description', '')}*\n\n"
                md += f"**⏱️ Prep time:** {recipe_data.get('prep_time', '-')} | **🍳 Cook time:** {recipe_data.get('cook_time', '-')} | **👪 Servings:** {recipe_data.get('servings', '-')}\n\n"
                md += f"**📊 Macros (per serving):** Calories: {recipe_data.get('calories', '-')} | Protein: {recipe_data.get('protein', '-')} | Carbs: {recipe_data.get('carbs', '-')} | Fat: {recipe_data.get('fat', '-')}\n\n"
                md += "#### 🛒 Ingredients:\n"
                for item in recipe_data.get("ingredients", []):
                    md += f"- {item}\n"
                md += "\n#### 👨‍🍳 Instructions:\n"
                for i, item in enumerate(recipe_data.get("instructions", [])):
                    md += f"{i+1}. {item}\n"
                tip = recipe_data.get("tip", "")
                if tip:
                    md += f"\n#### 💡 Chef's Tip:\n{tip}\n"

                tab1, tab2, tab3 = st.tabs(["🎨 Recipe Card", "📝 Regular Text", "💬 Chef Chat History"])
                with tab1:
                    st.markdown(inline_html, unsafe_allow_html=True)
                with tab2:
                    st.markdown(md)
                with tab3:
                    saved_chat = recipe_data.get("chat_history", [])
                    if not saved_chat:
                        st.info("No chat history saved for this recipe.")
                    else:
                        for msg in saved_chat:
                            with st.chat_message(msg["role"]):
                                st.markdown(msg["content"])
    st.stop()

# Main Interface
st.title(t["title"])
st.markdown(t["subtitle"])

st.header(t["generator"])

search_mode = st.radio(
    t["search_mode"],
    [t["by_ingredients"], t["by_recipe"], t["by_image"], t["by_visual"]],
    horizontal=True
)

col1, col2 = st.columns(2)

with col1:
    uploaded_image = None
    if search_mode == t["by_ingredients"]:
        # Voice Input for Ingredients
        ing_btn_col, _ = st.columns([1, 2])
        with ing_btn_col:
            ing_audio = mic_recorder(start_prompt=t["speak"], stop_prompt=t["stop"], key='mic_ingredients', format='wav')
        if ing_audio and ing_audio['id'] != st.session_state.get('last_ing_id', ''):
            with st.spinner(t["transcribing"]):
                transcribed_text = transcribe_audio(ing_audio['bytes'], current_speech_lang)
                if transcribed_text:
                    if st.session_state.ingredients_input:
                        st.session_state.ingredients_input += f", {transcribed_text}"
                    else:
                        st.session_state.ingredients_input = transcribed_text
            st.session_state['last_ing_id'] = ing_audio['id']
            st.rerun()

        ingredients = st.text_area(t["ingredients"], key="ingredients_input", placeholder=t["ingredients_ph"], height=150, help=t["ingredients_help"])
        recipe_name = ""
    elif search_mode == t["by_recipe"]:
        # Voice Input for Recipe Name
        rec_btn_col, _ = st.columns([1, 2])
        with rec_btn_col:
            rec_audio = mic_recorder(start_prompt=t["speak"], stop_prompt=t["stop"], key='mic_recipe', format='wav')
        if rec_audio and rec_audio['id'] != st.session_state.get('last_rec_id', ''):
            with st.spinner(t["transcribing"]):
                transcribed_text = transcribe_audio(rec_audio['bytes'], current_speech_lang)
                if transcribed_text:
                    if st.session_state.recipe_name_input:
                        st.session_state.recipe_name_input += f" {transcribed_text}"
                    else:
                        st.session_state.recipe_name_input = transcribed_text
            st.session_state['last_rec_id'] = rec_audio['id']
            st.rerun()

        recipe_name = st.text_input(t["recipe_name"], key="recipe_name_input", placeholder=t["recipe_name_ph"], help=t["recipe_name_help"])
        ingredients = ""
    elif search_mode == t["by_visual"]:
        st.markdown(f"**{t['visual_help']}**")
        
        visual_ingredients = st.multiselect(
            "",
            options=COMMON_INGREDIENTS,
            default=[],
            label_visibility="collapsed"
        )
        
        selected_str = ", ".join(visual_ingredients)
        ingredients = st.text_area(t["ingredients"], value=selected_str, key="visual_ing_input", height=80)
        recipe_name = ""
    else:
        # File Input for Image
        uploaded_image = st.file_uploader(t["upload_image"], type=["jpg", "jpeg", "png"], help=t["upload_image_help"])
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Preview", use_container_width=True)
        ingredients = ""
        recipe_name = ""
        
    meal_type = st.selectbox(t["meal_type"], t["meal_type_options"])
    max_time = st.slider(t["max_time"], min_value=10, max_value=120, value=45, step=5)

with col2:
    # Voice Input for Cuisine
    cui_btn_col, _ = st.columns([1, 2])
    with cui_btn_col:
        cui_audio = mic_recorder(start_prompt=t["speak"], stop_prompt=t["stop"], key='mic_cuisine', format='wav')
    if cui_audio and cui_audio['id'] != st.session_state.get('last_cui_id', ''):
        with st.spinner(t["transcribing"]):
            transcribed_text = transcribe_audio(cui_audio['bytes'], current_speech_lang)
            if transcribed_text:
                if st.session_state.cuisine_input:
                    st.session_state.cuisine_input += f", {transcribed_text}"
                else:
                    st.session_state.cuisine_input = transcribed_text
        st.session_state['last_cui_id'] = cui_audio['id']
        st.rerun()

    cuisine = st.text_input(t["cuisine"], key="cuisine_input", placeholder=t["cuisine_ph"], help=t["cuisine_help"])
    
    # Voice Input for Dietary Preferences
    diet_btn_col, _ = st.columns([1, 2])
    with diet_btn_col:
        diet_audio = mic_recorder(start_prompt=t["speak"], stop_prompt=t["stop"], key='mic_dietary', format='wav')
    if diet_audio and diet_audio['id'] != st.session_state.get('last_diet_id', ''):
        with st.spinner(t["transcribing"]):
            transcribed_text = transcribe_audio(diet_audio['bytes'], current_speech_lang)
            if transcribed_text:
                if st.session_state.dietary_input:
                    st.session_state.dietary_input += f", {transcribed_text}"
                else:
                    st.session_state.dietary_input = transcribed_text
        st.session_state['last_diet_id'] = diet_audio['id']
        st.rerun()

    dietary_preferences = st.text_input(t["dietary"], key="dietary_input", placeholder=t["dietary_ph"], help=t["dietary_help"])
    
    skill_level = st.selectbox(t["skill_level"], t["skill_level_options"])

button_label = t.get("button_create") if search_mode == t["by_recipe"] else t["button"]
if st.button(button_label, use_container_width=True):
    if not gemini_api_key:
        st.error(t["error_api"])
    elif search_mode == t["by_ingredients"] and not ingredients:
        st.warning(t["warn_ing"])
    elif search_mode == t["by_recipe"] and not recipe_name:
        st.warning(t["warn_recipe"])
    elif search_mode == t["by_image"] and uploaded_image is None:
        st.warning(t["warn_image"])
    elif search_mode == t["by_visual"] and not ingredients:
        st.warning(t["warn_ing"])
    elif not cuisine:
        st.warning(t["warn_cui"])
    else:
        with st.spinner(t["spinner"]):
            try:
                # Initialize Gemini LLM
                llm = ChatGoogleGenerativeAI(
                    model="gemini-flash-latest",
                    temperature=0.7,
                    google_api_key=gemini_api_key
                )
                
                # Define Template
                if search_mode in [t["by_ingredients"], t["by_visual"]]:
                    template = """You are an expert, creative chef.
Please reply entirely in this language: {language}.

A user wants to cook a meal with the following ingredients:
{ingredients}

They want the dish to be inspired by this cuisine:
{cuisine}

Meal Type: {meal_type}
Skill Level: {skill_level}
Maximum Cooking Time: {max_time} minutes
Dietary Preferences (if any): {dietary_preferences}

Please craft a delicious, well-structured recipe matching these criteria. You can assume the user has basic pantry staples like salt, pepper, oil, butter, and water.
Translate all content into {language}.

CRITICAL: You MUST format your response as a valid JSON object. Do not use Markdown blocks (like ```json), just output the raw JSON object.
Use the following exact keys:
{{
  "title": "[Catchy Recipe Title]",
  "description": "[A brief 1-2 sentence appetizing description of the dish]",
  "prep_time": "[Time]",
  "cook_time": "[Time]",
  "servings": "[Number]",
  "calories": "[Number kcal]",
  "protein": "[Number g]",
  "carbs": "[Number g]",
  "fat": "[Number g]",
  "badges": ["[Badge 1]", "[Badge 2]"],
  "ingredients": ["[Ingredient 1]", "[Ingredient 2]"],
  "instructions": ["[Step 1]", "[Step 2]"],
  "tip": "[A chef's tip]",
  "image_prompt": "[A highly detailed English prompt describing the visual appearance of the dish for an AI image generator]"
}}
"""
                    input_vars = ["language", "ingredients", "cuisine", "meal_type", "skill_level", "max_time", "dietary_preferences"]
                elif search_mode == t["by_recipe"]:
                    template = """You are an expert, creative chef.
Please reply entirely in this language: {language}.

A user wants to cook a specific dish named:
{recipe_name}

They want it to be authentic to or inspired by this cuisine:
{cuisine}

Meal Type: {meal_type}
Skill Level: {skill_level}
Maximum Cooking Time: {max_time} minutes
Dietary Preferences (if any): {dietary_preferences}

Please provide a detailed, authentic recipe for this dish.
Translate all content into {language}.

CRITICAL: You MUST format your response as a valid JSON object. Do not use Markdown blocks (like ```json), just output the raw JSON object.
Use the following exact keys:
{{
  "title": "[Catchy Recipe Title]",
  "description": "[A brief 1-2 sentence appetizing description of the dish]",
  "prep_time": "[Time]",
  "cook_time": "[Time]",
  "servings": "[Number]",
  "calories": "[Number kcal]",
  "protein": "[Number g]",
  "carbs": "[Number g]",
  "fat": "[Number g]",
  "badges": ["[Badge 1]", "[Badge 2]"],
  "ingredients": ["[Ingredient 1]", "[Ingredient 2]"],
  "instructions": ["[Step 1]", "[Step 2]"],
  "tip": "[A chef's tip]",
  "image_prompt": "[A highly detailed English prompt describing the visual appearance of the dish for an AI image generator]"
}}
"""
                    input_vars = ["language", "recipe_name", "cuisine", "meal_type", "skill_level", "max_time", "dietary_preferences"]
                
                invoke_args = {
                    "language": selected_language,
                    "cuisine": cuisine,
                    "meal_type": meal_type,
                    "skill_level": skill_level,
                    "max_time": max_time,
                    "dietary_preferences": dietary_preferences if dietary_preferences else "None"
                }

                if search_mode == t["by_image"]:
                    image_bytes = uploaded_image.getvalue()
                    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                    img_type = uploaded_image.type
                    
                    image_template = """You are an expert, creative chef.
Please reply entirely in this language: {language}.

A user has provided an image of ingredients. Please identify the ingredients and craft a delicious recipe using them.
They want the dish to be inspired by this cuisine:
{cuisine}

Meal Type: {meal_type}
Skill Level: {skill_level}
Maximum Cooking Time: {max_time} minutes
Dietary Preferences (if any): {dietary_preferences}

Translate all content into {language}.

CRITICAL: You MUST format your response as a valid JSON object. Do not use Markdown blocks (like ```json), just output the raw JSON object.
Use the following exact keys:
{{
  "title": "[Catchy Recipe Title]",
  "description": "[A brief 1-2 sentence appetizing description of the dish]",
  "prep_time": "[Time]",
  "cook_time": "[Time]",
  "servings": "[Number]",
  "calories": "[Number kcal]",
  "protein": "[Number g]",
  "carbs": "[Number g]",
  "fat": "[Number g]",
  "badges": ["[Badge 1]", "[Badge 2]"],
  "ingredients": ["[Ingredient 1]", "[Ingredient 2]"],
  "instructions": ["[Step 1]", "[Step 2]"],
  "tip": "[A chef's tip]",
  "image_prompt": "[A highly detailed English prompt describing the visual appearance of the dish for an AI image generator]"
}}"""
                    text_prompt = PromptTemplate.from_template(image_template).format(**invoke_args)
                    
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{encoded_image}"}}
                        ]
                    )
                    response = llm.invoke([message])
                else:
                    # Create PromptTemplate
                    prompt = PromptTemplate(
                        input_variables=input_vars,
                        template=template
                    )
                    
                    # Create execution chain (LCEL syntax)
                    chain = prompt | llm
                    
                    # Execute chain
                    if search_mode in [t["by_ingredients"], t["by_visual"]]:
                        invoke_args["ingredients"] = ingredients
                    else:
                        invoke_args["recipe_name"] = recipe_name
    
                    response = chain.invoke(invoke_args)
                
                # Extract text content safely
                output = response.content
                if isinstance(output, list) and len(output) > 0:
                    output = output[0].get("text", str(output))
                
                # Clean up JSON if LLM wrapped it in markdown
                if output.startswith("```json"):
                    output = output.replace("```json", "", 1)
                if output.startswith("```"):
                    output = output.replace("```", "", 1)
                if output.endswith("```"):
                    output = output[:-3]
                output = output.strip()

                try:
                    recipe_data = json.loads(output)
                except json.JSONDecodeError:
                    st.error("Failed to parse recipe data. Please try again.")
                    st.stop()
                
                recipe_title = recipe_data.get("title", f"A delicious {cuisine} {meal_type} meal")
                
                # Determine image URL instantly using the English image prompt
                image_prompt = recipe_data.get("image_prompt", recipe_title)
                encoded_prompt = urllib.parse.quote(image_prompt + ", highly detailed, appetizing, professional food photography")
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                
                # Build regular markdown text for display
                markdown_output = f"### 🍽️ {recipe_title}\n\n"
                badges = recipe_data.get("badges", [])
                if badges:
                    markdown_output += "**Tags:** " + " ".join([f"`{b}`" for b in badges]) + "\n\n"
                markdown_output += f"*{recipe_data.get('description', '')}*\n\n"
                markdown_output += f"**⏱️ Prep time:** {recipe_data.get('prep_time', '-')} | **🍳 Cook time:** {recipe_data.get('cook_time', '-')} | **👪 Servings:** {recipe_data.get('servings', '-')}\n\n"
                markdown_output += f"**📊 Macros (per serving):** Calories: {recipe_data.get('calories', '-')} | Protein: {recipe_data.get('protein', '-')} | Carbs: {recipe_data.get('carbs', '-')} | Fat: {recipe_data.get('fat', '-')}\n\n"
                
                markdown_output += "#### 🛒 Ingredients:\n"
                for item in recipe_data.get("ingredients", []):
                    markdown_output += f"- {item}\n"
                
                markdown_output += "\n#### 👨‍🍳 Instructions:\n"
                for i, item in enumerate(recipe_data.get("instructions", [])):
                    markdown_output += f"{i+1}. {item}\n"
                
                tip = recipe_data.get("tip", "")
                if tip:
                    markdown_output += f"\n#### 💡 Chef's Tip:\n{tip}\n"
                
                # Render beautiful HTML card synchronously
                inline_html, standalone_html = render_recipe_card(recipe_data, image_url)
                
                # Generate clean text for audio reading synchronously
                clean_text = f"Recipe for {recipe_title}. "
                if badges:
                    clean_text += f"Tags: {', '.join(badges)}. "
                clean_text += f"{recipe_data.get('description', '')}. "
                clean_text += f"Preparation time: {recipe_data.get('prep_time', '')}. Cook time: {recipe_data.get('cook_time', '')}. Servings: {recipe_data.get('servings', '')}. "
                clean_text += f"Nutritional estimates per serving: {recipe_data.get('calories', 'unknown')} calories, {recipe_data.get('protein', 'unknown')} of protein, {recipe_data.get('carbs', 'unknown')} of carbs, and {recipe_data.get('fat', 'unknown')} of fat. "
                clean_text += "Ingredients: " + ", ".join(recipe_data.get("ingredients", [])) + ". "
                clean_text += "Instructions: "
                for i, item in enumerate(recipe_data.get("instructions", [])):
                    clean_text += f"Step {i+1}: {item} "
                if tip:
                    clean_text += f"Chef's Tip: {tip}."
                
                # RUN HEAVY TASKS IN PARALLEL
                with st.spinner("Finalizing your magical recipe (Generating Audio, Image, and PDF)... ✨"):
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        future_img = executor.submit(download_image, image_url)
                        future_audio = executor.submit(text_to_audio, clean_text, current_speech_lang)
                        future_pdf = executor.submit(generate_pdf_parallel, standalone_html)
                        
                        image_bytes = future_img.result()
                        audio_bytes = future_audio.result()
                        pdf_bytes = future_pdf.result()
                
                st.session_state.current_recipe = {
                    "recipe_title": recipe_title,
                    "cuisine": cuisine,
                    "image_url": image_url,
                    "recipe_data": recipe_data,
                    "markdown_output": markdown_output,
                    "inline_html": inline_html,
                    "standalone_html": standalone_html,
                    "image_bytes": image_bytes,
                    "audio_bytes": audio_bytes,
                    "pdf_bytes": pdf_bytes
                }
                
                # Clear chat history for the new recipe
                st.session_state.chat_history = []
                
                st.success(t["success"])
                st.snow()
            except Exception as e:
                st.error(f"{t['error_gen']}{e}")

if st.session_state.current_recipe:
    gr = st.session_state.current_recipe
    
    if st.session_state.cooking_mode_active:
        # Render Cooking Mode UI
        instructions = gr['recipe_data'].get('instructions', [])
        if not instructions:
            st.warning("No instructions found for this recipe.")
            if st.button("❌ Exit Cooking Mode"):
                st.session_state.cooking_mode_active = False
                st.rerun()
            st.stop()
            
        current_index = st.session_state.cooking_step_index
        if current_index >= len(instructions):
            current_index = len(instructions) - 1
            st.session_state.cooking_step_index = current_index
            
        st.markdown("<h1 style='text-align: center;'>👨‍🍳 Cooking Mode</h1>", unsafe_allow_html=True)
        
        progress = (current_index + 1) / len(instructions)
        st.progress(progress)
        st.markdown(f"<p style='text-align: center; font-weight: bold;'>Step {current_index + 1} of {len(instructions)}</p>", unsafe_allow_html=True)
        
        step_text = instructions[current_index]
        st.markdown(f'''
            <div style="background-color: rgba(255, 255, 255, 0.9); padding: 40px 20px; border-radius: 15px; border: 2px solid #e63946; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: 30px 0; text-align: center;">
                <h2 style="font-size: 2.2em; line-height: 1.5; color: #333; margin: 0;">{step_text}</h2>
            </div>
        ''', unsafe_allow_html=True)
        
        audio_key = f"audio_step_{current_index}"
        if audio_key not in st.session_state:
            with st.spinner("Generating audio for this step..."):
                audio_bytes = text_to_audio(step_text, current_speech_lang)
                st.session_state[audio_key] = audio_bytes
        
        if st.session_state.get(audio_key):
            st.audio(st.session_state[audio_key], format="audio/mp3", autoplay=True)
            
        nav1, nav2, nav3 = st.columns(3)
        with nav1:
            if current_index > 0:
                if st.button("⬅️ Previous Step", use_container_width=True):
                    st.session_state.cooking_step_index -= 1
                    st.rerun()
        with nav2:
            if st.button("❌ Exit Cooking Mode", use_container_width=True):
                st.session_state.cooking_mode_active = False
                st.rerun()
        with nav3:
            if current_index < len(instructions) - 1:
                if st.button("Next Step ➡️", use_container_width=True, type="primary"):
                    st.session_state.cooking_step_index += 1
                    st.rerun()
            else:
                if st.button("🎉 Finish Cooking", use_container_width=True, type="primary"):
                    st.session_state.cooking_mode_active = False
                    st.balloons()
                    st.rerun()
        st.stop()
        
    if st.button("👨‍🍳 Start Cooking Mode", use_container_width=True, type="primary"):
        st.session_state.cooking_mode_active = True
        st.session_state.cooking_step_index = 0
        for key in list(st.session_state.keys()):
            if key.startswith("audio_step_"):
                del st.session_state[key]
        st.rerun()
        
    if gr["audio_bytes"]:
        st.audio(gr["audio_bytes"], format="audio/mp3")
    
    # Create Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Regular Recipe", "🎨 Recipe Card", t.get("chat_title", "💬 Chef Chat")])
    
    with tab1:
        style_box = st.container(border=True)
        style_box.markdown(gr["markdown_output"])
        if gr["image_bytes"]:
            st.image(gr["image_bytes"], caption=f"AI Generated Image for: {gr['recipe_title']}", use_container_width=True)
            
    with tab2:
        st.markdown(gr["inline_html"], unsafe_allow_html=True)

    with tab3:
        st.subheader(t.get("chat_title", "💬 Chef Chat"))
        st.markdown(t.get("chat_subtitle", "Got a question about this recipe? Need a substitution? Ask away!"))
        
        # Voice Input for Chat
        chat_btn_col, _ = st.columns([1, 5])
        with chat_btn_col:
            chat_audio = mic_recorder(start_prompt=t["speak"], stop_prompt=t["stop"], key='mic_chat', format='wav')
            
        new_prompt = None
        
        # Process audio input if available
        if chat_audio and chat_audio['id'] != st.session_state.get('last_chat_id', ''):
            with st.spinner(t["transcribing"]):
                transcribed_text = transcribe_audio(chat_audio['bytes'], current_speech_lang)
                if transcribed_text:
                    new_prompt = transcribed_text
            st.session_state['last_chat_id'] = chat_audio['id']

        # Display existing chat messages
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Chat text input
        typed_prompt = st.chat_input(t.get("chat_placeholder", "Ask a question..."))
        if typed_prompt:
            new_prompt = typed_prompt
            
        if new_prompt:
            st.session_state.chat_history.append({"role": "user", "content": new_prompt})
            with st.chat_message("user"):
                st.markdown(new_prompt)
                
            recipe_context = f"You are a helpful AI chef assistant. The user is currently viewing this recipe:\nTitle: {gr['recipe_title']}\nDescription: {gr['recipe_data'].get('description', '')}\nIngredients: {', '.join(gr['recipe_data'].get('ingredients', []))}\nInstructions: {' '.join(gr['recipe_data'].get('instructions', []))}\n\nAnswer the user's questions concisely and helpfully. Translate your answer to the user's language if necessary."
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    chat_llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.7, google_api_key=gemini_api_key)
                    lc_messages = [SystemMessage(content=recipe_context)]
                    for msg in st.session_state.chat_history:
                        if msg["role"] == "user":
                            lc_messages.append(HumanMessage(content=msg["content"]))
                        else:
                            lc_messages.append(AIMessage(content=msg["content"]))
                            
                    try:
                        response = chat_llm.invoke(lc_messages)
                        reply = response.content
                        
                        # Extract text safely if it's a list (e.g. [{'type': 'text', 'text': '...'}])
                        if isinstance(reply, list) and len(reply) > 0:
                            # Try to find the text part, otherwise fallback to string representation
                            text_parts = [p.get("text", "") for p in reply if isinstance(p, dict) and "text" in p]
                            if text_parts:
                                reply = "".join(text_parts)
                            else:
                                reply = str(reply)
                        elif not isinstance(reply, str):
                            reply = str(reply)
                            
                        st.markdown(reply)
                        
                        # Ensure we only store string content in the chat history
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error connecting to Chef Chat: {e}")
    
    # Display Save & Download Buttons
    col_save, col_down = st.columns(2)
    
    def handle_save(title, cui, img, data_dict, chat_history):
        # Inject the current chat history into the recipe data dict
        data_dict["chat_history"] = chat_history
        save_recipe(title, cui, img, json.dumps(data_dict))
        st.toast("Recipe and Chat History saved to your Cookbook!", icon="📖")
        
    with col_save:
        st.button("❤️ Save to Cookbook", on_click=handle_save, args=(gr["recipe_title"], gr["cuisine"], gr["image_url"], gr["recipe_data"], st.session_state.chat_history), use_container_width=True)
    
    with col_down:
        if gr["pdf_bytes"]:
            st.download_button(
                label=t["download"] + " (PDF Recipe Card)",
                data=gr["pdf_bytes"],
                file_name="recipe_card.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("Failed to generate PDF recipe card.")
