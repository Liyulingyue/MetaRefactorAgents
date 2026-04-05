import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import CreateAgent from './pages/CreateAgent';
import Lineage from './pages/Lineage';
import PortViewer from './pages/PortViewer';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/chat/:agentId" element={<Chat />} />
          <Route path="/create" element={<CreateAgent />} />
          <Route path="/lineage" element={<Lineage />} />
          <Route path="/system" element={<PortViewer />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
