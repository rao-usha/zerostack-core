# Quick Start Guide

Get up and running with ZeroStack in minutes!

## Prerequisites Check

- Python 3.8+ installed? Check with: `python3 --version`
- Node.js 18+ installed? Check with: `node --version`
- npm installed? Check with: `npm --version`

## Installation Steps

### Option 1: Automated Setup (Recommended)

```bash
# Run the install script from project root
./scripts/install_all.sh
```

This will:
1. Set up Python virtual environment
2. Install all backend dependencies
3. Install all frontend dependencies

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend Setup (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

## Using the Platform

### 1. Access the Application
Open your browser and go to: `http://localhost:3000`

### 2. Upload Sample Data
- Click on "Data Explorer" in the sidebar
- Upload a CSV file
- Or use the example data if available

### 3. Explore Features

#### Data Explorer
- Browse uploaded datasets
- View data previews and statistics
- Run SQL queries on your data

#### Data Dictionary
- Define column metadata
- Document data schemas
- Track data lineage

#### Distillation Workbench
- Create distilled datasets for ML training
- Configure distillation parameters
- Export processed data

#### ML Development
- Build predictive models
- Track experiments
- Evaluate model performance

#### Chat with AI
- Go to "Chat" section
- Select your dataset (optional)
- Ask questions like:
  - "What columns are in my dataset?"
  - "What's the average sales?"
  - "Show me correlations"
  - "How many rows are there?"

## Example Queries for Chat

Try these questions in the Chat interface:
- "What columns do I have?"
- "How many rows are in my dataset?"
- "What's the mean of sales?"
- "Show me the maximum value in quantity"
- "Are there any missing values?"
- "What correlations exist?"

## Troubleshooting

### Backend won't start
- Check if port 8000 is available: `lsof -i :8000` (or `netstat -ano | findstr 8000` on Windows)
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.8+)

### Frontend won't start
- Check if port 3000 is available: `lsof -i :3000` (or `netstat -ano | findstr 3000` on Windows)
- Make sure node_modules is installed: `npm install`
- Check Node version: `node --version` (should be 18+)

### CORS Errors
- Make sure backend is running on port 8000
- Check that frontend is trying to connect to correct API URL
- Verify CORS settings in `backend/main.py`

### Import Errors in Backend
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

1. Upload your own data
2. Explore all features
3. Generate insights for your business
4. Build predictive models
5. Check out the API documentation at `http://localhost:8000/docs`

Enjoy exploring your data with ZeroStack!
