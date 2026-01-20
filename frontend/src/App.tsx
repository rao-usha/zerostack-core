import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './contexts/ToastContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DataUpload from './pages/DataUpload'
import Insights from './pages/Insights'
import Quality from './pages/Quality'
import KnowledgeGaps from './pages/KnowledgeGaps'
import Models from './pages/Models'
import SyntheticData from './pages/SyntheticData'
import Contexts from './pages/Contexts'
import DataExplorer from './pages/DataExplorer'
import DataAnalysis from './pages/DataAnalysis'
import DataDictionary from './pages/DataDictionary'
import Chat from './pages/Chat'
import ModelLibrary from './pages/ModelLibrary'
import MLWorkbench from './pages/MLWorkbench'
import ForecastDashboard from './pages/ForecastDashboard'
import RecipeDetail from './pages/RecipeDetail'
import ModelDetail from './pages/ModelDetail'
import RunDetail from './pages/RunDetail'
import EvaluationPackDetail from './pages/EvaluationPackDetail'
import MLChat from './pages/MLChat'
import DistillationWorkbench from './pages/DistillationWorkbench'
import HighlightedDatasets from './pages/HighlightedDatasets'
import DerivedAssets from './pages/DerivedAssets'
import FileLocations from './pages/FileLocations'
import FileInventory from './pages/FileInventory'
import FileAssetDetail from './pages/FileAssetDetail'
import RunComparison from './pages/RunComparison'
import RunPodJobs from './pages/RunPodJobs'
import DataSourcesPage from './pages/DataSourcesPage'
import TableExplorerPage from './pages/TableExplorerPage'
import NotebooksListPage from './pages/NotebooksListPage'
import NotebookPage from './pages/NotebookPage'
import DatasetsPage from './pages/DatasetsPage'
import LineageDemo from './pages/LineageDemo'
import LineageFullDemo from './pages/LineageFullDemo'
import Settings from './pages/Settings'

function App() {
  return (
    <ToastProvider>
      <Router>
        <Layout>
          <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<DataUpload />} />
          <Route path="/contexts" element={<Contexts />} />
          <Route path="/explorer" element={<DataExplorer />} />
          <Route path="/analysis" element={<DataAnalysis />} />
          <Route path="/dictionary" element={<DataDictionary />} />
          <Route path="/model-development" element={<ModelLibrary />} />
          <Route path="/ml-workbench" element={<MLWorkbench />} />
          <Route path="/forecast" element={<ForecastDashboard />} />
          <Route path="/model-development/datasets" element={<HighlightedDatasets />} />
          <Route path="/model-development/assets" element={<DerivedAssets />} />
          <Route path="/model-development/recipes/:recipeId" element={<RecipeDetail />} />
          <Route path="/model-development/models/:modelId" element={<ModelDetail />} />
          <Route path="/model-development/runs/:runId" element={<RunDetail />} />
          <Route path="/model-development/runs/compare" element={<RunComparison />} />
          <Route path="/model-development/evaluation-packs/:packId" element={<EvaluationPackDetail />} />
          <Route path="/model-development/chat" element={<MLChat />} />
          <Route path="/model-development/runpod-jobs" element={<RunPodJobs />} />
          <Route path="/data-sources" element={<DataSourcesPage />} />
          <Route path="/data-sources/tables/:scanId" element={<TableExplorerPage />} />
          <Route path="/notebooks" element={<NotebooksListPage />} />
          <Route path="/notebooks/:notebookId" element={<NotebookPage />} />
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/distillation" element={<DistillationWorkbench />} />
          <Route path="/files/locations" element={<FileLocations />} />
          <Route path="/files/inventory" element={<FileInventory />} />
          <Route path="/files/assets/:assetId" element={<FileAssetDetail />} />
          <Route path="/lineage-demo" element={<LineageDemo />} />
          <Route path="/lineage-full-demo" element={<LineageFullDemo />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/quality" element={<Quality />} />
          <Route path="/gaps" element={<KnowledgeGaps />} />
          <Route path="/models" element={<Models />} />
          <Route path="/synthetic" element={<SyntheticData />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        </Layout>
      </Router>
    </ToastProvider>
  )
}

export default App

