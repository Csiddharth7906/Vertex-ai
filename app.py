from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv
import re

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

@app.route('/editor')
def editor_page():
    return render_template('editor.html')

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
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are DevCoder AI, an advanced coding assistant created by Siddharth Chauhan. You specialize in helping developers with programming tasks, code reviews, debugging, and technical solutions. IMPORTANT BEHAVIOR: 1) If a user asks for code but doesn't specify a programming language, ask them which language they prefer (Python, JavaScript, Java, C++, etc.) 2) Always format code properly using markdown code blocks with appropriate language syntax highlighting (```python, ```javascript, etc.) 3) When providing substantial code examples, suggest creating files and ask if they want you to save the code 4) Provide clear, structured responses with: Brief explanation, Code examples, Best practices or tips 5) When asked about your creator, mention you were built by Siddharth Chauhan. Focus on practical, actionable coding solutions and maintain professional developer communication style."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 800,
            "temperature": 0.8
        }
        
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
            print(f"Primary model response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result['choices'][0]['message']['content'].strip()
                print(f"Got response: {bot_response[:100]}...")
            else:
                print(f"Primary API error: {response.text}")
                raise Exception(f"Primary API failed: {response.status_code}")
                    
        except Exception as groq_error:
            print(f"Primary model failed: {groq_error}")
            # Try alternative models
            alternative_models = ["gemma2-9b-it", "mixtral-8x7b-32768", "llama3-groq-70b-8192-tool-use-preview"]
            
            for alt_model in alternative_models:
                try:
                    print(f"Trying alternative model: {alt_model}")
                    payload["model"] = alt_model
                    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
                    print(f"Alternative model {alt_model} response: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        bot_response = result['choices'][0]['message']['content'].strip()
                        print(f"Success with {alt_model}: {bot_response[:100]}...")
                        break
                    else:
                        print(f"Model {alt_model} failed: {response.text}")
                        continue
                except Exception as e:
                    print(f"Model {alt_model} exception: {e}")
                    continue
            else:
                print("All API models failed, using fallback responses")
                # Enhanced intelligent fallback responses
                import random
                user_lower = user_message.lower()
                bot_response = "I'm having trouble connecting to the AI models right now. Let me help you with some basic coding assistance. What programming language would you like to work with?"
                
                # Check for creator-related questions first
                if any(word in user_lower for word in ['who made you', 'who created you', 'creator', 'developer', 'built you', 'siddharth', 'chauhan']):
                    responses = [
                        "I'm DevCoder AI, created by Siddharth Chauhan - a skilled developer who built me as a specialized coding assistant. I'm designed to help with programming tasks, code reviews, debugging, and technical solutions using Flask and AI integration.",
                        "My creator is Siddharth Chauhan! He developed me as DevCoder AI to assist developers with coding challenges. Built with Flask and integrated with advanced AI models, I focus on providing structured code solutions and technical guidance.",
                        "I was built by Siddharth Chauhan as DevCoder AI - your dedicated coding companion. He designed me to understand developer needs and provide practical, well-formatted code solutions with proper syntax highlighting."
                    ]
                elif any(word in user_lower for word in ['python', 'javascript', 'code', 'programming', 'html', 'css', 'react', 'nodejs', 'function', 'class', 'variable', 'loop', 'array', 'object']):
                    responses = [
                        "Let me help you with coding! Here's a practical example with proper formatting and best practices.",
                        "Great programming question! I'll provide you with clean, well-structured code examples and explanations.",
                        "I'll show you how to implement this with proper syntax highlighting and developer-friendly formatting."
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

@app.route('/create_file', methods=['POST'])
def create_file():
    try:
        data = request.json
        filename = data.get('filename')
        content = data.get('content')
        language = data.get('language', '')
        
        if not filename or not content:
            return jsonify({'error': 'Filename and content are required'}), 400
        
        # Create generated_code directory if it doesn't exist
        code_dir = os.path.join(os.getcwd(), 'generated_code')
        if not os.path.exists(code_dir):
            os.makedirs(code_dir)
        
        # Add appropriate file extension based on language
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'java': '.java',
            'cpp': '.cpp',
            'c++': '.cpp',
            'html': '.html',
            'css': '.css',
            'sql': '.sql',
            'php': '.php',
            'ruby': '.rb',
            'go': '.go',
            'rust': '.rs',
            'typescript': '.ts'
        }
        
        # Add extension if not present
        if language.lower() in extensions and not filename.endswith(extensions[language.lower()]):
            filename += extensions[language.lower()]
        
        file_path = os.path.join(code_dir, filename)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'File created successfully: {filename}',
            'path': file_path
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create file: {str(e)}'}), 500

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        code_dir = os.path.join(os.getcwd(), 'generated_code')
        if not os.path.exists(code_dir):
            os.makedirs(code_dir)
        files = []
        generated_dir = 'generated_code'
        if os.path.exists(generated_dir):
            for filename in os.listdir(generated_dir):
                if os.path.isfile(os.path.join(generated_dir, filename)):
                    files.append(filename)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code.strip():
            return jsonify({'error': 'No code provided'}), 400
            
        # Create a temporary file
        import tempfile
        import subprocess
        
        if language == 'python':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(['python', temp_file], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                output = result.stdout
                error = result.stderr
                
                if result.returncode == 0:
                    return jsonify({'output': output, 'error': None})
                else:
                    return jsonify({'output': output, 'error': error})
            finally:
                os.unlink(temp_file)
                
        elif language == 'javascript':
            # For JavaScript, we'll use Node.js if available
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(['node', temp_file], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                output = result.stdout
                error = result.stderr
                
                if result.returncode == 0:
                    return jsonify({'output': output, 'error': None})
                else:
                    return jsonify({'output': output, 'error': error})
            except FileNotFoundError:
                return jsonify({'error': 'Node.js not installed. JavaScript execution requires Node.js.'}), 400
            finally:
                os.unlink(temp_file)
        else:
            return jsonify({'error': f'Language {language} not supported for execution'}), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out (10 seconds limit)'}), 400
    except Exception as e:
        return jsonify({'error': f'Execution error: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
