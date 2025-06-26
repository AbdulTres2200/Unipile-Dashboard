# 📬 Unipile Dashboard — Unified Timeline Importer

This project powers a unified messaging dashboard by importing messages from **Gmail** and **LinkedIn** using the [Unipile API](https://www.unipile.com/). It fetches, parses, and stores communication history into a centralized timeline for easy access and analysis.

---

## 🚀 Features

- 🔗 Connect and sync Gmail & LinkedIn accounts via Unipile
- 📥 Import all messages (emails & LinkedIn DMs)
- 🧠 Intelligent parsing: sender, recipient, content, timestamp, threads
- 🗂️ Store messages into a database (e.g. Supabase)
- 🔄 Track import progress with statuses: fetching, processing, completed
- ✅ Handles both one-time full imports and future incremental syncs (extendable)
- 🌐 Frontend dashboard to view connected accounts and import status

---

## 🛠 Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** (REST API server)
- **Supabase** (PostgreSQL + Storage + Auth)
- **Unipile API** (for Gmail & LinkedIn data access)
- `httpx` for async HTTP requests
- `asyncio` for concurrency

### Frontend
- **React.js**
- **Tailwind CSS**
- **Axios** for API calls
- **Vite** for fast dev server

---

## 📂 Project Structure

```
unipile-dashboard/
├── backend/
│   ├── services/
│   │   ├── complete_import_service.py
│   │   ├── supabase_service.py
│   │   └── unipile_service.py
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   └── index.html
├── connected_accounts.json
└── README.md
```

---

## ⚙️ Backend Setup

### 1. Clone the repo

```bash
git clone https://github.com/AbdulTres2200/Unipile-Dashboard.git
cd Unipile-Dashboard/backend
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, manually install:

```bash
pip install fastapi uvicorn httpx
```

### 4. Configure API Keys

Edit `unipile_service.py` and `supabase_service.py`:

```python
# unipile_service.py
api_key = "YOUR_UNIPILE_API_KEY"
base_url = "https://api.unipile.com:PORT/api/v1"

# supabase_service.py
supabase_url = "https://your-project.supabase.co"
supabase_key = "your-service-role-key"
```

### 5. Run the backend server

```bash
uvicorn main:app --reload
```

---

## 🌐 Frontend Setup

### 1. Navigate to frontend

```bash
cd ../frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Run development server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## 🧪 Sample Usage

- Connect a Unipile account (manually or via API)
- Use `/api/messages/import/start/{account_id}` to begin import
- Check progress at `/api/messages/import/status/{account_id}`
- View results in the frontend under unified timeline

---

## 🧭 Future Roadmap

- [ ] Automatic background sync (CRON or webhook)
- [ ] Enhanced error logging and retries
- [ ] OAuth-based connection flow for Unipile
- [ ] Message search and filter in frontend
- [ ] CSV/JSON export of unified messages

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/awesome`)
3. Commit your changes (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/awesome`)
5. Open a pull request

---

## 📄 License

MIT License © [Abdul Moiz](https://github.com/AbdulTres2200)

---


