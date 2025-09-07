# AI Chatbot

A simple and beautiful AI chatbot built with Python, Flask, and OpenAI's GPT API. Perfect for beginners!

## Features

- 🤖 AI-powered conversations using OpenAI's GPT-3.5-turbo
- 💬 Beautiful and responsive web interface
- 🎨 Modern gradient design
- ⚡ Real-time chat experience
- 📱 Mobile-friendly

## Setup Instructions

### 1. Install Python
If you don't have Python installed:
- Go to [python.org](https://python.org/downloads/)
- Download Python 3.8 or newer
- Install it (make sure to check "Add Python to PATH")

### 2. Get OpenAI API Key
1. Go to [OpenAI's website](https://platform.openai.com/)
2. Sign up for an account
3. Go to API Keys section
4. Create a new API key
5. Copy the key (you'll need it in step 4)

### 3. Install Dependencies
Open Command Prompt in this folder and run:
```bash
pip install -r requirements.txt
```

### 4. Set up your API Key
1. Copy the `.env.example` file and rename it to `.env`
2. Open the `.env` file
3. Replace `your_openai_api_key_here` with your actual OpenAI API key

### 5. Run the Chatbot
In Command Prompt, run:
```bash
python app.py
```

### 6. Open in Browser

## How to Use

1. Type your message in the input box at the bottom
2. Press Enter or click "Send"
3. Wait for the AI to respond
4. Continue the conversation!

## Troubleshooting

**"Module not found" error:**
- Make sure you installed the requirements: `pip install -r requirements.txt`

**"Invalid API key" error:**
- Check that your `.env` file has the correct Groq API key
- Make sure there are no extra spaces in the key

**Can't access localhost:5000:**
- Make sure the app is running (you should see "Running on http://0.0.0.0:5000")
- Try `http://127.0.0.1:5000` instead

## Customization

You can customize the chatbot by editing:
- `app.py` - Change the AI's personality in the system message
- `templates/index.html` - Modify the appearance and styling
- Add more features like conversation history, different AI models, etc.

## Cost Note

This chatbot uses OpenAI's API, which charges per use. GPT-3.5-turbo is very affordable (about $0.002 per 1K tokens), but keep track of your usage on the OpenAI dashboard.

Enjoy chatting with your AI! 🚀
