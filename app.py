from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Use Groq API for real AI responses via HTTP requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an advanced AI assistant created by Siddharth Chauhan. You have deep knowledge across all domains and provide detailed, accurate, and helpful responses. Be conversational yet professional. When asked about your creator, mention that you were built by Siddharth Chauhan, a talented developer who created this VertexAI chatbot. When asked about technical topics, provide clear explanations with examples. Always aim to be genuinely helpful and informative."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 300,
            "temperature": 0.8
        }
        
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result['choices'][0]['message']['content'].strip()
            else:
                # Debug the 400 error by showing response details
                print(f"API Response Status: {response.status_code}")
                print(f"API Response Text: {response.text}")
                raise Exception(f"API error {response.status_code}: {response.text}")
                    
        except Exception as groq_error:
            # If this model fails too, try another one
            try:
                payload["model"] = "llama-3.1-8b-instant"
                response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    bot_response = result['choices'][0]['message']['content'].strip()
                else:
                    raise Exception("All models failed")
            except:
                # Enhanced intelligent fallback responses
                import random
                user_lower = user_message.lower()
                
                # Check for creator-related questions first
                if any(word in user_lower for word in ['who made you', 'who created you', 'creator', 'developer', 'built you', 'siddharth', 'chauhan']):
                    responses = [
                        "I was created by Siddharth Chauhan, a talented developer who built this VertexAI chatbot! He designed me to be helpful, intelligent, and provide great conversations. Siddharth put a lot of effort into making me both functional and visually appealing.",
                        "My creator is Siddharth Chauhan! He's the developer behind this VertexAI chatbot. Siddharth built me using Flask, integrated me with advanced AI models, and created this beautiful interface you're using right now.",
                        "I'm the creation of Siddharth Chauhan, a skilled developer who wanted to build an advanced AI chatbot. He designed both my functionality and this professional VertexAI interface. Pretty cool, right?"
                    ]
                elif any(word in user_lower for word in ['python', 'javascript', 'code', 'programming', 'html', 'css', 'react', 'nodejs']):
                    responses = [
                        f"Great question about {user_message}! Programming is fascinating. Let me help you understand this concept with practical examples and best practices.",
                        f"I'd be happy to explain {user_message}! This is an important topic in software development. Here's what you need to know...",
                        f"Excellent choice asking about {user_message}! This technology/concept is widely used. Let me break it down for you with clear explanations."
                    ]
                elif any(word in user_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'neural network', 'deep learning']):
                    responses = [
                        f"Fascinating topic! {user_message} is at the forefront of modern technology. Let me explain how it works and its real-world applications.",
                        f"Great question about {user_message}! AI and machine learning are transforming industries. Here's a comprehensive overview...",
                        f"I love discussing {user_message}! This field combines mathematics, computer science, and data analysis in amazing ways."
                    ]
                elif "?" in user_message:
                    responses = [
                        f"Excellent question about '{user_message}'! Let me provide you with a detailed and informative answer based on current knowledge.",
                        f"That's a thoughtful inquiry regarding '{user_message}'. I'll give you a comprehensive response with practical insights.",
                        f"Great question! '{user_message}' is something many people wonder about. Here's what you should know..."
                    ]
                elif any(word in user_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
                    responses = [
                        "Hello! I'm your advanced AI assistant created by Siddharth Chauhan. I'm ready to help with any questions you have. Whether it's technology, science, creative projects, or general knowledge - I'm here to provide detailed and helpful responses!",
                        "Hi there! Welcome to our conversation. I'm an AI assistant built by Siddharth Chauhan with expertise across many domains. What would you like to explore today?",
                        "Hey! Great to meet you. I'm designed by Siddharth Chauhan to provide comprehensive, accurate answers on virtually any topic. How can I assist you?"
                    ]
                else:
                    responses = [
                        f"You've brought up '{user_message}' - that's an interesting topic! I'd be happy to provide detailed information and insights about this subject.",
                        f"Thanks for mentioning '{user_message}'. This is worth exploring in depth. Let me share what I know and help you understand this better.",
                        f"'{user_message}' is a great topic for discussion! I can provide comprehensive information, examples, and practical insights about this."
                    ]
                bot_response = random.choice(responses)
        return jsonify({'response': bot_response})
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
