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
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
    return render_template('editor_clean.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        user_data = users_collection.find_one({'username': username})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            user = User(user_data)
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid username or password'})
            else:
                flash('Invalid username or password', 'error')
                return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
        
        # Check if user already exists
        if users_collection.find_one({'username': username}):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Username already exists'})
            else:
                flash('Username already exists', 'error')
                return render_template('signup.html')
        
        if users_collection.find_one({'email': email}):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email already registered'})
            else:
                flash('Email already registered', 'error')
                return render_template('signup.html')
        
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
            if request.is_json:
                return jsonify({'success': True, 'message': 'Account created successfully'})
            else:
                flash('Account created successfully!', 'success')
                return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Failed to create account'})
            else:
                flash('Failed to create account', 'error')
                return render_template('signup.html')
    
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

@app.route('/api/chat', methods=['POST'])
def api_chat():
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
                    "content": "You are DevCoder AI created by Siddharth Chauhan, a specialized coding assistant. IMPORTANT CONTEXT RULES: 1) Only provide code when user asks programming-related questions (like 'write a function', 'create a website', 'build an app', 'hello world program', etc.) 2) For casual greetings ('hi', 'hello', 'how are you') respond conversationally without code 3) For general questions, provide helpful answers without unnecessary code examples 4) CODING RULES (only when code is requested): Never ask 'what language?' - choose appropriate language or provide multiple 5) For website requests, create SEPARATE files: index.html, style.css, script.js 6) For 'hello world' requests, provide code in multiple languages 7) Always suggest proper filenames 8) Keep coding responses concise - code first, brief explanation after 9) For GUI requests, create complete working code 10) Make reasonable assumptions, don't ask for clarification 11) Use proper code blocks with language tags"
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
            'response': 'File created successfully: ' + filename,
            'path': file_path
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create file: {str(e)}'}), 500
@app.route('/execute', methods=['POST'])
@login_required
def execute_code():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'javascript')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        if language == 'javascript':
            # Execute JavaScript using Node.js
            import subprocess
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with Node.js
                result = subprocess.run(['node', temp_file], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                output = result.stdout
                error = result.stderr
                
                return jsonify({
                    'output': output,
                    'error': error,
                    'success': result.returncode == 0
                })
                
            except FileNotFoundError:
                return jsonify({
                    'output': '',
                    'error': 'Node.js not installed. Please install Node.js to run JavaScript.',
                    'success': False
                })
            finally:
                os.unlink(temp_file)
                
        elif language == 'python':
            # Execute Python code
            import subprocess
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with Python
                result = subprocess.run(['python', temp_file], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                
                output = result.stdout
                error = result.stderr
                
                return jsonify({
                    'output': output,
                    'error': error,
                    'success': result.returncode == 0
                })
                
            finally:
                os.unlink(temp_file)
                
        elif language == 'java':
            # Execute Java code
            import subprocess
            import tempfile
            import os
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            java_file = os.path.join(temp_dir, 'Main.java')
            
            # Write Java code
            with open(java_file, 'w') as f:
                f.write(code)
            
            try:
                # Compile Java
                compile_result = subprocess.run(['javac', java_file], 
                                             capture_output=True, 
                                             text=True, 
                                             timeout=10)
                
                if compile_result.returncode != 0:
                    return jsonify({
                        'output': '',
                        'error': compile_result.stderr,
                        'success': False
                    })
                
                # Run Java
                class_file = os.path.join(temp_dir, 'Main')
                run_result = subprocess.run(['java', '-cp', temp_dir, 'Main'], 
                                         capture_output=True, 
                                         text=True, 
                                         timeout=10)
                
                return jsonify({
                    'output': run_result.stdout,
                    'error': run_result.stderr,
                    'success': run_result.returncode == 0
                })
                
            except FileNotFoundError:
                return jsonify({
                    'output': '',
                    'error': 'Java not installed. Please install Java JDK to run Java code.',
                    'success': False
                })
            finally:
                # Clean up
                import shutil
                shutil.rmtree(temp_dir)
        
        else:
            return jsonify({'error': f'Language {language} not supported'}), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'output': '',
            'error': 'Code execution timed out (10 seconds limit)',
            'success': False
        })
    except Exception as e:
        return jsonify({
            'output': '',
            'error': f'Execution error: {str(e)}',
            'success': False
        })

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
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500


@app.route('/terminal', methods=['POST'])
def terminal_command():
    """Execute terminal commands"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'error': 'No command provided', 'success': False})
    
    # Security: Block dangerous commands
    dangerous_commands = ['rm -rf', 'del /f', 'format', 'shutdown', 'reboot', 'sudo rm', 'rm -r /', 'dd if=']
    if any(dangerous in command.lower() for dangerous in dangerous_commands):
        return jsonify({'error': 'Command blocked for security reasons', 'success': False})
    
    try:
        import subprocess
        import os
        
        # Change to project directory for commands
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            cwd=project_dir
        )
        
        output = result.stdout
        error = result.stderr
        
        # Combine output and error for display
        full_output = ""
        if output:
            full_output += output
        if error:
            if full_output:
                full_output += "\n"
            full_output += error
        
        return jsonify({
            'output': full_output,
            'success': result.returncode == 0,
            'return_code': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Command timed out (60 seconds limit)',
            'success': False
        })
    except Exception as e:
        return jsonify({
            'output': '',
            'error': f'Error executing command: {str(e)}',
            'success': False
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
