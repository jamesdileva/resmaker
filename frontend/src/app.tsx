import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { KnowledgeBaseContextProvider } from './contexts/KnowledgeBaseContext';
import { BuilderContextProvider } from './contexts/BuilderContext';
import { UIContextProvider } from './contexts/UIContext';

export function App() {
  return (
    <UIContextProvider>
      <KnowledgeBaseContextProvider>
        <BuilderContextProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </BuilderContextProvider>
      </KnowledgeBaseContextProvider>
    </UIContextProvider>
  );
}
