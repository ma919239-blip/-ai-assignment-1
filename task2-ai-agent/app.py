"""
AI Code Helper - Flask Web Application
Uses Groq API (free LLM) to help users with Python code
Author: [Your Name]
Roll No: [Your Roll Number]
"""

from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get API key from environment variable (NOT hardcoded!)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


# ==========================================
# SYSTEM PROMPT - Defines Agent's Role
# ==========================================
SYSTEM_PROMPT = """You are CodeHelper AI, a friendly and expert Python programming assistant.

Your role:
- Explain Python code in simple, beginner-friendly language
- Debug Python code and point out errors with explanations
- Suggest improvements and best practices
- Write Python code examples when asked
- Answer Python-related questions clearly

Rules:
- Always explain your reasoning
- Use code blocks with proper formatting
- If code has errors, show the corrected version
- Be encouraging and supportive
- If asked about non-Python topics, politely redirect to Python
- Handle these types of queries well:
  1. Code explanation requests
  2. Code debugging/fixing
  3. Code writing requests
  4. Concept explanations
  5. Best practice suggestions
"""


def get_ai_response(user_message, chat_history):
    """
    Send user message to Groq API and get AI response
    
    Args:
        user_message (str): The user's input message
        chat_history (list): Previous conversation messages
    
    Returns:
        str: AI assistant's response
    """
    # Build message list with system prompt + history + new message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add chat history (last 10 messages to keep context manageable)
    messages.extend(chat_history[-10:])
    
    # Add the new user message
    messages.append({"role": "user", "content": user_message})
    
    # Set up the API request
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",  # Free model on Groq
        "messages": messages,
        "temperature": 0.7,    # Creativity level (0-1)
        "max_tokens": 2048,    # Max response length
        "top_p": 0.9
    }
    
    try:
        # Send request to Groq API
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Extract and return the AI's response
        result = response.json()
        ai_message = result["choices"][0]["message"]["content"]
        return ai_message
        
    except requests.exceptions.Timeout:
        return "⏰ Error: Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "🔌 Error: Cannot connect to API. Check your internet."
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "🔑 Error: Invalid API key. Check your .env file."
        elif response.status_code == 429:
            return "⚠️ Error: Rate limit reached. Wait a moment and try again."
        else:
            return f"❌ Error: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


# ==========================================
# FLASK ROUTES
# ==========================================

@app.route("/")
def home():
    """Render the main page"""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat requests from the frontend"""
    # Get user message from the request
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    # Validate input
    if not user_message:
        return jsonify({"error": "Please enter a message!"}), 400
    
    if len(user_message) > 2000:
        return jsonify({"error": "Message too long! Max 2000 characters."}), 400
    
    # Get chat history from the request
    chat_history = data.get("history", [])
    
    # Get AI response
    ai_response = get_ai_response(user_message, chat_history)
    
    # Return response as JSON
    return jsonify({
        "response": ai_response,
        "status": "success"
    })


@app.route("/health")
def health():
    """Simple health check endpoint"""
    return jsonify({
        "status": "running",
        "api_key_configured": bool(GROQ_API_KEY)
    })


# ==========================================
# RUN THE APP
# ==========================================
if __name__ == "__main__":
    # Check if API key is set
    if not GROQ_API_KEY:
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        print("   Create a .env file with: GROQ_API_KEY=your_key_here")
    else:
        print("✅ API Key found!")
        print("🚀 AI Code Helper starting at: http://127.0.0.1:5000")
    
    app.run(debug=True, port=5000)