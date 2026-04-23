# Secure PDF Distribution and Traceability System

This project is a professional-grade secure document distribution platform that uses AI-powered semantic watermarking, diagonal email overlays, and invisible metadata fingerprints to ensure document traceability and prevent unauthorized leaks.

## 🚀 Quick Setup for Team Members (Windows)

If you have just cloned the repository, follow these steps:

1. **Install Node.js & Python**: Ensure you have Node.js (v18+) and Python (3.11 or 3.12 recommended) installed.
2. **Run Automatic Setup**: 
   - Double-click the `setup.bat` file in the project folder.
   - **OR** run `npm run setup` in your terminal.
3. **Start the Application**: 
   - Run `npm start` in the terminal.
   - The **Frontend** will be at: `http://localhost:5173`
   - The **Backend** will be at: `http://localhost:8000`

---

## 🛠 Troubleshooting Common Issues

### ❌ Error: "Failed to build asyncpg" or "Building wheels"
This usually happens because `asyncpg` (the database driver) needs to be compiled, but your computer lacks the necessary tools.
- **Fix 1 (Recommended):** Use **Python 3.11 or 3.12**. These versions have pre-built versions of `asyncpg` that don't need compilation on Windows.
- **Fix 2:** Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and select "Desktop development with C++".
- **Fix 3:** Try installing a slightly older version that might have a wheel for your Python version:
  ```bash
  .\.venv\Scripts\python.exe -m pip install asyncpg==0.29.0
  ```

### ❌ Error: "Pip 26.0.1 is available"
This is just a notification. Your current pip version will work fine. To make the message go away, run:
```bash
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

---

## 🏗 System Architecture

The application is built using a modern, high-performance stack:

- **Frontend:** React.js (Vite) + Tailwind CSS (Premium 3D Aesthetics)
- **Backend:** Python FastAPI (Asynchronous performance)
- **Database:** PostgreSQL (with SQLAlchemy Async)
- **AI Engine:** Google Gemini AI (for semantic paraphrasing and leak detection)
- **PDF Engine:** ReportLab & PyMuPDF (for watermarking and security)

## 🔒 Key Security Features

- **Semantic Fingerprinting:** Every recipient receives a uniquely paraphrased version of the document.
- **Diagonal Watermarking:** Recipient's email is tiled across every page of the document.
- **Access Logs:** Every attempt to copy, print, or view is logged and notified.
- **Leak Detection Hub:** Upload a leaked snippet to identify exactly which recipient it came from.

---

## 📁 Project Structure

```text
root/
├── frontend/               # React + Vite application
├── backend/                # FastAPI application
├── .venv/                  # Python Virtual Environment (created after setup)
├── setup.bat               # One-click setup for Windows
├── package.json            # Root configuration & scripts
└── run.py                  # Backend entry point
```

## 👥 Team Information

- **Level:** College / Academic Project
- **Scope:** Secure Digital Rights Management (DRM)
