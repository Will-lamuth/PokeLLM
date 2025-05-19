# Pokémon Chatbot UI

## 📦 Structure
- `backend/`: Contains `server.py` and your existing LLM logic as `your_existing_script.py`
- `frontend/`: HTML/CSS/JS interface for the chatbot
- `pokemon_gen12_moveset.json`: Your Gen 1 & 2 legal move database

## 🚀 How to Run

### 1. Start Backend API
```bash
cd backend
pip install flask flask-cors
python server.py
```

### 2. Start Frontend Server
```bash
cd frontend
python3 -m http.server 8080
```

### 3. Visit in Browser
Go to: [http://localhost:8080](http://localhost:8080)

Chat with your Pokémon assistant!
