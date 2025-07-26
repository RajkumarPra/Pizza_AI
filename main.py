from agents.ordering_agent import place_order, track_order
from agents.scheduler_agent import schedule_delivery
from utils.config import FLASH_MODEL
import speech_recognition as sr

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now:")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        if not text.strip():
            print("❌ No speech detected.")
            return ""
        print("🗣️ You said:", text)
        return text.lower()
    except Exception as e:
        print("❌ Voice error:", e)
        return ""

def interpret(command):
    prompt = f"""
You are an intelligent assistant for a pizza ordering system.

Given this user message: "{command}"

Determine whether the user wants to place a pizza order or track an order.

Respond ONLY in this JSON format:
{{ "intent": "order" }} or {{ "intent": "track" }}
"""
    response = FLASH_MODEL.generate_content(prompt)
    cleaned = response.text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        intent_json = eval(cleaned)
        return intent_json.get("intent", "unknown")
    except Exception as e:
        print("⚠️ Gemini intent parsing failed:", e)
        return "unknown"

def main():
    print("👋 Welcome to Mission Pizza!")
    print("💬 Would you like to type or speak? (type/speak)")
    method = input("👉 Your choice:\n> ").strip().lower()

    if method == "speak":
        print("🎤 Speak your full request (e.g. 'Please deliver a large Margherita pizza' or 'Where is my order')")
        command = listen()

        if not command.strip():
            print("⚠️ No voice input received. Please try again.")
            return

        intent = interpret(command)

        if intent not in ["order", "track"]:
            print("🤖 Sorry, I couldn’t understand your intent.")
            return

        if intent == "order":
            result = place_order(command)
            if "order_id" in result:
                print("✅ Order placed!")
                print("🆔 Order ID:", result["order_id"])
                scheduled = schedule_delivery(result)
                print(f"📅 {scheduled['message']}")
            else:
                print("❌", result.get("message"))
                if result.get("raw"):
                    print("Gemini Raw Output:", result["raw"])

        elif intent == "track":
            order_id = input("🆔 Please enter your Order ID:\n> ")
            result = track_order(order_id)
            if "order_id" in result:
                print("✅ Order Details:", result)
            else:
                print("❌", result.get("message"))

    elif method == "type":
        user_input = input("💬 What would you like to say? (e.g. 'I want pizza', 'Track my order')\n> ").strip()

        if not user_input:
            print("⚠️ No input provided. Try again.")
            return

        intent = interpret(user_input)

        if intent not in ["order", "track"]:
            print("🤖 Sorry, I couldn’t understand your intent.")
            return

        if intent == "order":
            result = place_order(user_input)
            if "order_id" in result:
                print("✅ Order placed!")
                print("🆔 Order ID:", result["order_id"])
                scheduled = schedule_delivery(result)
                print(f"📅 {scheduled['message']}")
            else:
                print("❌", result.get("message"))
                if result.get("raw"):
                    print("Gemini Raw Output:", result["raw"])

        elif intent == "track":
            order_id = input("🆔 Please enter your Order ID:\n> ")
            result = track_order(order_id)
            if "order_id" in result:
                print("✅ Order Details:", result)
            else:
                print("❌", result.get("message"))

    else:
        print("❌ Invalid input. Please choose 'type' or 'speak'.")

if __name__ == "__main__":
    main()
