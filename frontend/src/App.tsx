import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
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
import Distillation from './pages/Distillation'
import Chat from './pages/Chat'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<DataUpload />} />
          <Route path="/contexts" element={<Contexts />} />
          <Route path="/distillation" element={<Distillation />} />
          <Route path="/explorer" element={<DataExplorer />} />
          <Route path="/analysis" element={<DataAnalysis />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/quality" element={<Quality />} />
          <Route path="/gaps" element={<KnowledgeGaps />} />
          <Route path="/models" element={<Models />} />
          <Route path="/synthetic" element={<SyntheticData />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

