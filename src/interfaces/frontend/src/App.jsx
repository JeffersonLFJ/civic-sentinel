import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';

// Placeholder Pages
import AuditoriaPage from './features/auditoria/AuditoriaPage';
import DocumentosPage from './features/documents/DocumentosPage';
import StagingPage from './features/staging/StagingPage';
import SettingsPage from './features/settings/SettingsPage';

import { ChatPage } from './features/chat/ChatPage';
import InspectorPage from './features/inspector/InspectorPage';
const GenericPage = ({ title }) => <div className="p-10 text-xl font-bold">{title} Page (Coming Soon)</div>;

function App() {
  return (
    <BrowserRouter basename="/admin">
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="auditoria" element={<AuditoriaPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="documentos" element={<DocumentosPage />} />
          <Route path="quarentena" element={<StagingPage />} />
          <Route path="inspetor" element={<InspectorPage />} />
          <Route path="cerebro" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
