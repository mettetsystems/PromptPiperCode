import { BrowserRouter, Navigate, Route, Routes, useParams } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { NewSessionPage } from "./pages/NewSessionPage";
import { PrecisionPage } from "./pages/PrecisionPage";
import { RegistryDetailPage } from "./pages/RegistryDetailPage";
import { RegistryPage } from "./pages/RegistryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SessionRedirectPage, SessionWorkflowPage } from "./pages/SessionWorkflowPage";

function PrecisionWorkflowPage() {
  const { sessionId = "" } = useParams();
  return <PrecisionPage sessionId={sessionId} />;
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="sessions/new" element={<NewSessionPage />} />
          <Route path="sessions/:sessionId" element={<SessionRedirectPage />} />
          <Route path="sessions/:sessionId/clarify" element={<SessionWorkflowPage step="clarify" />} />
          <Route path="sessions/:sessionId/edit" element={<SessionWorkflowPage step="edit" />} />
          <Route
            path="sessions/:sessionId/similarity"
            element={<SessionWorkflowPage step="similarity" />}
          />
          <Route path="sessions/:sessionId/optimize" element={<SessionWorkflowPage step="optimize" />} />
          <Route
            path="sessions/:sessionId/precision"
            element={<PrecisionWorkflowPage />}
          />
          <Route path="sessions/:sessionId/export" element={<SessionWorkflowPage step="export" />} />
          <Route path="sessions/:sessionId/complete" element={<SessionWorkflowPage step="complete" />} />
          <Route path="registry" element={<RegistryPage />} />
          <Route path="registry/:promptId" element={<RegistryDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
