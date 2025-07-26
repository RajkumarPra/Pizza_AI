import google.generativeai as genai

genai.configure(api_key="AIzaSyB--cRz8uvbUfzDjFtsWIaR01hJkb61AvA")  # <-- Replace this

FLASH_MODEL = genai.GenerativeModel("models/gemini-2.5-flash")
