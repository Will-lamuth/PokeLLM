from flask import Flask, request, jsonify, render_template
from chatbot_core import detect_pokemon_names, build_grounded_prompt, query_llm, messages, model_name


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    detected = detect_pokemon_names(user_input)
    grounded_prompt = build_grounded_prompt(user_input, detected) if detected else user_input
    messages.append({"role": "user", "content": grounded_prompt})
    print("flask")
    reply = query_llm(model_name, messages)
    print("flask2")
    messages.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
