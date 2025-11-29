# Quick Start Guide

Get up and running with the AI Native Data Platform in minutes!

## Prerequisites Check

- Python 3.8+ installed? Check with: `python3 --version`
- Node.js 18+ installed? Check with: `node --version`
- npm installed? Check with: `npm --version`

## Installation Steps

### Option 1: Automated Setup (Recommended)

```bash
# Make the start script executable (if not already)
chmod +x start.sh

# Run the start script
./start.sh
```

This will:
1. Set up Python virtual environment
2. Install all backend dependencies
3. Install all frontend dependencies
4. Start both servers automatically

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
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
- Click on "Upload Data" in the sidebar
- Use the sample file: `example_data/sample_sales_data.csv`
- Or upload your own CSV file

### 3. Explore Features

#### Generate Insights
- Go to "Insights" page
- Select your uploaded dataset
- Enter context (e.g., "retail business")
- Click "Generate Insights"
- View trends, correlations, and recommendations

#### Build Predictive Models
- Navigate to "Predictive Models"
- Select dataset and target column (e.g., "sales")
- Choose model type
- Click "Build Predictive Model"
- Review feature importance and performance

#### Chat with AI
- Go to "Chat" section
- Select your dataset (optional)
- Ask questions like:
  - "What columns are in my dataset?"
  - "What's the average sales?"
  - "Show me correlations"
  - "How many rows are there?"

#### Check Data Quality
- Navigate to "Data Quality"
- Select your dataset
- View quality scores and issues
- Get recommendations

#### Identify Knowledge Gaps
- Go to "Knowledge Gaps"
- Select dataset
- Review identified gaps
- See recommendations

#### Generate Synthetic Data
- Navigate to "Synthetic Data"
- Select source dataset
- Set number of rows
- Generate privacy-safe synthetic data

#### 🆕 Explore Data Distillation
- Navigate to "Distillation" tab
- Browse AI-generated contexts and variants
- Explore pre-built distillation datasets
- View distillation pipeline statistics
- Discover retail, insurance, and finance domains

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
- Check if port 8000 is available: `lsof -i :8000`
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.8+)

### Frontend won't start
- Check if port 3000 is available: `lsof -i :3000`
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
5. Use synthetic data for testing

Enjoy exploring your data with AI!

