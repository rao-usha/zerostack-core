# 🎉 ZeroStack - Installation Complete - Next Steps

## ✅ What's Installed

All packages have been successfully installed:
- ✅ **Node.js 18+** - Frontend runtime
- ✅ **Python 3.8+** - Backend runtime
- ✅ **Backend packages** - FastAPI, Pandas, Scikit-learn, etc.
- ✅ **Frontend packages** - React, TypeScript, Tailwind CSS, etc.

## 🚀 Start the Application

You need to start both servers in separate terminal windows:

### Terminal 1 - Start Backend
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Start Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

## 🌐 Access the Platform

Once both servers are running, open your browser:

**http://localhost:3000**

You should see the ZeroStack dashboard!

## 📊 Quick Test

1. Click **"Data Explorer"** in the sidebar
2. Upload a sample CSV file
3. Navigate to **"Insights"** to see AI-generated analysis
4. Try the **"Chat"** feature to ask questions about your data

## 📝 Available Features

Once running, you can:

- **Data Explorer** - Browse and analyze your datasets
- **Data Dictionary** - Define and document your data schema
- **Distillation Workbench** - Create distilled datasets for ML
- **ML Development** - Build and train machine learning models
- **Chat** - Ask questions in natural language
- **Model Library** - Manage and deploy trained models

## 🛠 Troubleshooting

### Backend won't start
```bash
cd backend
source venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"
uvicorn main:app --reload
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### Check installation status
```bash
./scripts/check_setup.sh
```

### Stop servers
```bash
# Stop backend (port 8000)
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows PowerShell:
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess

# Stop frontend (port 3000)
# Linux/Mac:
lsof -ti:3000 | xargs kill -9

# Windows PowerShell:
Stop-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess
```

## 📚 Documentation

- `docs/development.md` - Development guide
- `docs/guides/QUICKSTART.md` - Quick start guide
- `docs/setup/DATABASE_SETUP.md` - Database configuration
- `docs/api.md` - API reference

## 🔗 Quick Links

Once running:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (Swagger UI)

## ✨ Sample Queries to Try

In the Chat interface:
- "What columns are in my dataset?"
- "What's the average sales?"
- "Show me correlations"
- "Are there any missing values?"
- "What's the maximum value in quantity?"

Enjoy your AI-powered data platform! 🚀
