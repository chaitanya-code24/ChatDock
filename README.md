# 💬 ChatDock

ChatDock is a no-code platform that lets you build and embed AI-powered chatbots for your business in just a few simple steps. Whether you want a support bot, FAQ assistant, or a content-based helper — ChatDock helps you do it without writing a single line of code.

## 🚀 Features

- ✅ Create a chatbot by defining its goal (used as the context prompt)
- 📄 Upload your own documents or generate content from a prompt
- 🤖 Integrates with LLaMA/Groq API for real-time intelligent responses
- 🔗 Get a custom embed link or script to place the bot on your website
- 🧠 Context-aware and optimized for business use cases

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit (for now, can be migrated to React if needed)
- **Backend**: Python (FastAPI planned), integrated with Groq API + LLaMA models
- **Database**: Firebase / MongoDB (for user data and uploaded files)
- **Auth**: Google/Firebase Authentication (planned)
- **Hosting**: Streamlit Cloud / Render / Railway (TBD)

---

## 📦 How It Works

1. **Set Chatbot Goal** – Define the chatbot’s purpose or target behavior.
2. **Add Knowledge** – Upload docs or generate content from a prompt.
3. **Train & Preview** – Instantly preview how your chatbot responds.
4. **Embed** – Get a link or HTML snippet to place on your site.
5. **Manage** – Track usage, edit knowledge base, and retrain if needed.

---

## 🧪 Run Locally

```bash
git clone https://github.com/yourusername/chatdock.git
cd chatdock
pip install -r requirements.txt
streamlit run app.py
