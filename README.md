# JARVIS — Autonomous Windows Desktop Assistant

A modular Python desktop assistant for Windows featuring natural-language command execution via Google Gemini, voice recognition, spoken feedback, system diagnostics, SQLite memory, and a PyQt5 HUD interface.

## Setup Instructions (Windows)
1. Extract `jarvis_windows.zip` to a normal user folder (such as `C:\Users\cyber\Desktop`).
2. Open PowerShell inside `jarvis_windows` and create a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create `.env` and insert your Gemini API key:
   ```powershell
   Set-Content -Path .env -Value "GEMINI_API_KEY=YOUR_KEY_HERE" -Encoding ascii
   ```
4. Launch JARVIS:
   ```powershell
   python main.py
   ```
