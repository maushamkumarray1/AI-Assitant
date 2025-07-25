import os
import requests
from flask import Flask, request, jsonify, render_template
import datetime

app = Flask(__name__)

# The API key will be automatically provided by the Canvas environment.
# Leave this as an empty string if using secrets manager.
GEMINI_API_KEY = "AIzaSyCuRCWkDPU24fa34dtA9YxGD21jwxIbaDQ"

@app.route("/")
def home():
    """Renders the index.html template for the home page."""
    return render_template("index.html")

@app.route("/api", methods=["POST"])
def api():
    """
    Handles API requests to interact with the Gemini model.
    It takes a 'function' (question, summary, creative) and a 'prompt'
    from the request, formats the prompt, and sends it to the Gemini API.
    """
    try:
        print("✅ API route hit")
        data = request.json
        print("🔹 Received data:", data)

        user_function = data.get("function")
        user_prompt = data.get("prompt")

        if not user_function or not user_prompt:
            return jsonify({"reply": "Error: Missing 'function' or 'prompt'"}), 400

        prompt_map = {
            "question": f"Answer the following question:\n{user_prompt}",
            "summary": f"Summarize this:\n{user_prompt}",
            "creative": f"Be creative. Write something based on:\n{user_prompt}"
        }

        final_prompt = prompt_map.get(user_function, user_prompt)
        print("🔸 Prompt to Gemini:", final_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": final_prompt}
                    ]
                }
            ]
        }

        res = requests.post(url, headers=headers, json=payload)

        if res.status_code != 200:
            print("❌ Gemini API error:", res.text)
            return jsonify({"reply": f"Gemini API Error: {res.text}"}), 500

        response_data = res.json()
        reply = ""
        if response_data.get("candidates") and len(response_data["candidates"]) > 0:
            if response_data["candidates"][0].get("content") and \
               response_data["candidates"][0]["content"].get("parts") and \
               len(response_data["candidates"][0]["content"]["parts"]) > 0:
                reply = response_data["candidates"][0]["content"]["parts"][0].get("text", "")
        
        if not reply:
            print("❌ Gemini API returned no text content.")
            return jsonify({"reply": "Gemini API returned no text content."}), 500

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"reply": f"Internal Server Error: {str(e)}"}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handles feedback submission from the user.
    Appends the feedback with a timestamp to a 'feedback.txt' file.
    """
    try:
        data = request.json
        user_feedback = data.get("feedback", "")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("feedback.txt", "a") as f:
            f.write(f"[{timestamp}] {user_feedback}\n")
        return jsonify({"status": "Feedback recorded"})
    except Exception as e:
        print("❌ Feedback error:", str(e))
        return jsonify({"status": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    print(">>> Starting Flask app...")
    port = int(os.environ.get("PORT", 5000))  # ✅ for Render or other services
    app.run(debug=True, host="0.0.0.0", port=port)
