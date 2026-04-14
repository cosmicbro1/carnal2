import os
import json
import pathlib
import ssl
from flask import Flask, render_template, request, jsonify
from carnal2 import (
    chat_once, SYSTEM_PROMPT, MEMORY, SETTINGS, PDF_KNOWLEDGE,
    generate_image, build_tarot_prompt, ROOT, write_json, read_json, AGENTS_AVAILABLE
)

if AGENTS_AVAILABLE:
    from agents import toolkit, execute_agent_action

app = Flask(__name__, template_folder=".", static_folder=".")

# In-memory chat history per session
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


@app.route("/")
def index():
    """Serve the chat interface."""
    return render_template("web_chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat endpoint."""
    global chat_history
    data = request.json
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # Handle special commands
    if user_message.lower().startswith(":remember "):
        fact = user_message[10:].strip()
        if fact:
            MEMORY.setdefault("facts", []).append(fact)
            write_json(ROOT / "memory.json", MEMORY)
            return jsonify({"reply": "Noted. Memory updated."})
        return jsonify({"reply": "Give me something to remember."})
    
    if user_message.lower() == ":showmem":
        return jsonify({"memory": MEMORY})
    
    # Normal chat
    chat_history.append({"role": "user", "content": user_message})
    
    try:
        reply = chat_once(chat_history)
        chat_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"ERROR in /api/chat: {error_msg}")
        print(traceback_str)
        return jsonify({
            "error": error_msg,
            "hint": "Check your OpenAI API key in .env file or OPENAI_BASE_URL for local LLM",
            "debug": traceback_str[:200]  # First 200 chars of traceback
        }), 500


@app.route("/api/image", methods=["POST"])
def api_image():
    """Generate image from prompt."""
    data = request.json
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
    
    try:
        image_path = generate_image(prompt)
        return jsonify({"image_path": image_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/card", methods=["POST"])
def api_card():
    """Generate tarot card artwork."""
    data = request.json
    card_name = data.get("card", "").strip()
    style_hint = data.get("style", "").strip()
    
    if not card_name:
        return jsonify({"error": "Empty card name"}), 400
    
    try:
        prompt = build_tarot_prompt(card_name, style_hint)
        image_path = generate_image(prompt)
        return jsonify({"image_path": image_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/memory", methods=["GET"])
def get_memory():
    """Get current memory state."""
    return jsonify(MEMORY)


@app.route("/api/memory", methods=["POST"])
def update_memory():
    """Add a fact to memory."""
    data = request.json
    fact = data.get("fact", "").strip()
    
    if not fact:
        return jsonify({"error": "Empty fact"}), 400
    
    MEMORY.setdefault("facts", []).append(fact)
    write_json(ROOT / "memory.json", MEMORY)
    return jsonify({"success": True, "memory": MEMORY})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current settings."""
    return jsonify(SETTINGS)


@app.route("/api/agent/execute", methods=["POST"])
def agent_execute():
    """Execute an agent action."""
    if not AGENTS_AVAILABLE:
        return jsonify({"error": "Agents not available"}), 400
    
    data = request.json
    action_type = data.get("action", "").strip()
    
    if not action_type:
        return jsonify({"error": "No action specified"}), 400
    
    result = execute_agent_action(action_type, **data.get("params", {}))
    return jsonify({"result": result})


@app.route("/api/agent/logs", methods=["GET"])
def agent_logs():
    """Get agent execution logs."""
    if not AGENTS_AVAILABLE:
        return jsonify({"error": "Agents not available"}), 400
    
    return jsonify({"logs": toolkit.get_logs()})


if __name__ == "__main__":
    print("Carnal 2.0 Web Server")
    print("Access from iPhone on your WiFi at: http://<your-computer-ip>:8080")
    print("(Find your computer's IP: run 'ipconfig' and look for IPv4 address)")
    print("\nExample: http://192.168.1.50:8080")
    
    app.run(host="0.0.0.0", port=8080, debug=True)
