import google.generativeai as genai

genai.configure(api_key="enter your api key here")  # <-- Replace this

FLASH_MODEL = genai.GenerativeModel("models/gemini-2.5-flash")
