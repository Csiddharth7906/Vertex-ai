from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import requests
import json
import os
from dotenv import load_dotenv
import re
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGODB_URI)
db = client.devcoder_ai
users_collection = db.users

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    from bson import ObjectId
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/editor')
@login_required
def editor_page():
    return render_template('editor.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user_data = users_collection.find_one({'username': username})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            user = User(user_data)
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if user already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        if users_collection.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_doc = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            user = User(user_doc)
            login_user(user)
            return jsonify({'success': True, 'message': 'Account created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to create account'})
    
    return render_template('signup.html')


@app.route('/preview/<filename>')
def preview_file(filename):
    try:
        file_path = os.path.join('generated_code', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # For HTML files, fix relative paths to absolute paths
            if filename.endswith('.html'):
                # Replace relative CSS/JS links with absolute paths
                content = content.replace('href="style.css"', 'href="/generated_code/style.css"')
                content = content.replace('href="./style.css"', 'href="/generated_code/style.css"')
                content = content.replace('src="script.js"', 'src="/generated_code/script.js"')
                content = content.replace('src="./script.js"', 'src="/generated_code/script.js"')
                return content, 200, {'Content-Type': 'text/html'}
            elif filename.endswith('.css'):
                return content, 200, {'Content-Type': 'text/css'}
            elif filename.endswith('.js'):
                return content, 200, {'Content-Type': 'application/javascript'}
            else:
                return content
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/generated_code/<filename>')
def serve_generated_file(filename):
    try:
        file_path = os.path.join('generated_code', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Set proper content type
            if filename.endswith('.css'):
                return content, 200, {'Content-Type': 'text/css'}
            elif filename.endswith('.js'):
                return content, 200, {'Content-Type': 'application/javascript'}
            else:
                return content
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

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
                    "content": "You are DevCoder AI created by Siddharth Chauhan. CRITICAL RULES: 1) NEVER ask 'what language?' or 'what do you want to build?' - ALWAYS generate code immediately 2) For website requests, create SEPARATE files: index.html, style.css, script.js with proper linking 3) For 'hello world' requests, provide code in multiple languages at once 4) For 'write a program', create a complete working program immediately 5) ALWAYS suggest filenames like 'main.py', 'app.js', 'index.html' 6) Keep responses short - provide code first, brief explanation after 7) If user says 'in python' or 'in java', switch to that language but still provide code immediately 8) For GUI requests, create complete working GUI code 9) Never say 'I need more information' - make reasonable assumptions and code 10) Your job is to CODE, not to ask questions. 11) For websites, create multiple code blocks: ```html for HTML, ```css for CSS, ```javascript for JS files."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
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
                
        elif language == 'java':
            # For Java, compile and run
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Compile Java code
                compile_result = subprocess.run(['javac', temp_file], 
                                              capture_output=True, 
                                              text=True, 
                                              timeout=15)
                
                if compile_result.returncode != 0:
                    return jsonify({'output': '', 'error': f'Compilation Error:\n{compile_result.stderr}'})
                
                # Run compiled Java code
                class_name = os.path.basename(temp_file).replace('.java', '')
                class_file = temp_file.replace('.java', '.class')
                
                result = subprocess.run(['java', '-cp', os.path.dirname(temp_file), class_name], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                output = result.stdout
                error = result.stderr
                
                # Clean up class file
                if os.path.exists(class_file):
                    os.unlink(class_file)
                
                if result.returncode == 0:
                    return jsonify({'output': output, 'error': None})
                else:
                    return jsonify({'output': output, 'error': error})
                    
            except FileNotFoundError:
                return jsonify({'error': 'Java not installed. Java execution requires JDK.'}), 400
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        elif language in ['c', 'cpp']:
            # For C/C++, compile and run
            ext = '.c' if language == 'c' else '.cpp'
            compiler = 'gcc' if language == 'c' else 'g++'
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Compile C/C++ code
                exe_file = temp_file.replace(ext, '.exe')
                compile_result = subprocess.run([compiler, temp_file, '-o', exe_file], 
                                              capture_output=True, 
                                              text=True, 
                                              timeout=15)
                
                if compile_result.returncode != 0:
                    return jsonify({'output': '', 'error': f'Compilation Error:\n{compile_result.stderr}'})
                
                # Run compiled executable
                result = subprocess.run([exe_file], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                output = result.stdout
                error = result.stderr
                
                # Clean up executable
                if os.path.exists(exe_file):
                    os.unlink(exe_file)
                
                if result.returncode == 0:
                    return jsonify({'output': output, 'error': None})
                else:
                    return jsonify({'output': output, 'error': error})
                    
            except FileNotFoundError:
                return jsonify({'error': f'{compiler} not installed. {language.upper()} execution requires {compiler}.'}), 400
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        else:
            return jsonify({'error': f'Language {language} not supported for execution. Supported: Python, JavaScript, Java, C, C++'}), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out (10 seconds limit)'}), 400
    except Exception as e:
        return jsonify({'error': f'Execution error: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
