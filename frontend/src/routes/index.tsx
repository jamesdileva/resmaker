import { Route, Routes } from 'react-router-dom';
import { Layout } from '../components/layout';
import { Dashboard } from '../pages/Dashboard';
import { DutyStatementBuilder } from '../pages/DutyStatementBuilder';
import { ImportDocuments } from '../pages/ImportDocuments';
import { KnowledgeExplorer } from '../pages/KnowledgeExplorer';
import { ResumeBuilder } from '../pages/ResumeBuilder';
import { SOQBuilder } from '../pages/SOQBuilder';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/import" element={<ImportDocuments />} />
        <Route path="/resume" element={<ResumeBuilder />} />
        <Route path="/soq" element={<SOQBuilder />} />
        <Route path="/duty" element={<DutyStatementBuilder />} />
        <Route path="/explore" element={<KnowledgeExplorer />} />
      </Route>
    </Routes>
  );
}
