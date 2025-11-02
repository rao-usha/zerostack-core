# NEX.AI

## AI Native Data Platform

A comprehensive, AI-powered data platform that serves as a one-stop solution for all data-related needs in large organizations. This platform eliminates data governance concerns while providing powerful analytics, predictive modeling, and insights generation capabilities.

## Features

### 🚀 Core Capabilities

1. **Data Upload & Management**
   - Upload CSV datasets
   - Store and manage multiple datasets
   - Preview data before analysis

2. **Synthetic Data Generation**
   - Generate privacy-safe synthetic data from your datasets
   - Preserves statistical properties and distributions
   - No data governance issues - completely synthetic

3. **Predictive Modeling**
   - Build regression and classification models
   - Automatic feature importance analysis
   - Performance metrics (R², accuracy)

4. **AI-Powered Insights**
   - Automatic strategic insights generation
   - Trend identification
   - Anomaly detection
   - Correlation analysis
   - Context-aware recommendations

5. **Natural Language Chat Interface**
   - Ask questions about your data in plain English
   - Get instant answers about statistics, trends, and patterns
   - Dataset-aware responses

6. **Data Quality Assessment**
   - Comprehensive data quality scoring
   - Completeness analysis
   - Consistency checks
   - Accuracy validation
   - Issue identification and recommendations

7. **Knowledge Gap Identification**
   - Identify missing features and data gaps
   - Temporal coverage analysis
   - Data diversity assessment
   - Relationship gap detection
   - Actionable recommendations

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pandas** - Data manipulation and analysis
- **Scikit-learn** - Machine learning models
- **SQLite** - Lightweight database for data storage
- **NumPy, SciPy** - Numerical computations

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - API client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd /Users/usharao/Documents/Nex
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`

3. **Access the Application**
   Open your browser and navigate to `http://localhost:3000`

## Usage Guide

### 1. Upload Data
- Navigate to "Upload Data" section
- Select a CSV file
- File will be processed and stored

### 2. Generate Insights
- Go to "Insights" page
- Select your dataset
- Optionally provide context (e.g., "retail", "healthcare")
- Click "Generate Insights" to get AI-powered analysis

### 3. Build Predictive Models
- Navigate to "Predictive Models"
- Select dataset and target column
- Choose model type (regression or classification)
- View model performance and feature importance

### 4. Generate Synthetic Data
- Go to "Synthetic Data" page
- Select source dataset
- Specify number of rows to generate
- Get privacy-safe synthetic dataset

### 5. Assess Data Quality
- Navigate to "Data Quality"
- Select dataset for analysis
- Review quality scores and issues
- Get recommendations for improvement

### 6. Identify Knowledge Gaps
- Go to "Knowledge Gaps" page
- Select dataset
- View identified gaps and recommendations

### 7. Chat with AI
- Navigate to "Chat" section
- Select a dataset (optional)
- Ask questions in natural language
- Get instant answers about your data

## API Endpoints

### Data Management
- `POST /api/upload` - Upload a dataset
- `GET /api/datasets` - List all datasets
- `GET /api/dataset/{dataset_id}` - Get dataset details

### Synthetic Data
- `POST /api/synthetic/generate` - Generate synthetic data

### Predictive Modeling
- `POST /api/models/predictive` - Build a predictive model

### Insights
- `POST /api/insights/generate` - Generate strategic insights

### Chat
- `POST /api/chat` - Query data using natural language

### Data Quality
- `GET /api/quality/{dataset_id}` - Get data quality report

### Knowledge Gaps
- `GET /api/knowledge-gaps/{dataset_id}` - Identify knowledge gaps

## Project Structure

```
Nex/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database operations
│   ├── requirements.txt        # Python dependencies
│   ├── services/
│   │   ├── synthetic_data.py   # Synthetic data generation
│   │   ├── insights.py         # Insights generation
│   │   ├── chat.py            # Chat service
│   │   ├── data_quality.py    # Data quality analysis
│   │   └── knowledge_gaps.py  # Knowledge gap identification
│   └── data_storage/          # Database and data storage
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # React page components
│   │   ├── components/        # Reusable components
│   │   ├── api/               # API client
│   │   └── App.tsx            # Main app component
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## Features Highlights

### Privacy & Governance
- Synthetic data generation eliminates privacy concerns
- No sensitive data exposure in insights or models
- Local processing - data stays on your infrastructure

### AI-Powered
- Natural language queries
- Automatic insights generation
- Context-aware recommendations
- Intelligent gap identification

### Comprehensive Analytics
- Statistical analysis
- Predictive modeling
- Data quality assessment
- Relationship discovery

## Future Enhancements

- Real-time data streaming support
- Advanced ML model types (neural networks, etc.)
- Data visualization dashboards
- Export capabilities (PDF reports, CSV exports)
- Multi-user support with authentication
- Integration with cloud storage providers
- Advanced synthetic data techniques (GANs, VAEs)

## License

This is a prototype application for demonstration purposes.

## Support

For issues or questions, please check the code comments or API documentation at `http://localhost:8000/docs` when the backend is running.

