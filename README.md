# 🚀 Tensor-Titans

A lightweight API service built using **FastAPI**, designed for easy local setup and testing.

---

## 📦 Complete Setup & Run Guide

Follow all the steps below to set up and run the project locally.

---

### 🧰 Step 1 — Open Terminal in VS Code

Open your project folder in **VS Code**, then open the integrated terminal.

---

### 🐍 Step 2 — Create Virtual Environment

```bash
python -m venv venv


⚡ Step 3 — Activate Virtual Environment

On Windows:
venv\Scripts\activate

On Mac/Linux:
source venv/bin/activate

📚 Step 4 — Install Dependencies
pip install -r requirements.txt

▶️ Step 5 — Run the API Locally

From the project root directory, run:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

🌐 Access the Application

Once the server is running, open your browser and visit:

🔍 Health Check:
http://127.0.0.1:8000/health
📘 Interactive API Docs:
http://127.0.0.1:8000/docs
🧪 Testing the API

The /docs endpoint provides an interactive interface where you can:

View all available endpoints
Send test requests
Inspect responses in real-time

🛠 Tech Stack
FastAPI — API framework
Uvicorn — ASGI server

Python (venv) — Environment management
✅ Notes
Make sure Python is installed (preferably 3.8+)
Always activate the virtual environment before running the server
Use /docs for quick testing instead of external tools