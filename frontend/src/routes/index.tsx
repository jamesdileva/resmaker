import { Route, Routes } from 'react-router-dom';
import { Layout } from '../components/layout';
import { Dashboard } from '../pages/Dashboard';
import { ImportDocuments } from '../pages/ImportDocuments';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/import" element={<ImportDocuments />} />
      </Route>
    </Routes>
  );
}
