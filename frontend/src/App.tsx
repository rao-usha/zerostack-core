import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DataUpload from './pages/DataUpload'
import Insights from './pages/Insights'
import Quality from './pages/Quality'
import KnowledgeGaps from './pages/KnowledgeGaps'
import Models from './pages/Models'
import SyntheticData from './pages/SyntheticData'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<DataUpload />} />
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

