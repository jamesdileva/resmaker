import { HashRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { KnowledgeBaseContextProvider } from './contexts/KnowledgeBaseContext';
import { BuilderContextProvider } from './contexts/BuilderContext';
import { UIContextProvider } from './contexts/UIContext';

export function App() {
  return (
    <UIContextProvider>
      <KnowledgeBaseContextProvider>
        <BuilderContextProvider>
          {/* HashRouter keeps deep links working in packaged builds,
              where the app loads from file:// without a server. */}
          <HashRouter>
            <AppRoutes />
          </HashRouter>
        </BuilderContextProvider>
      </KnowledgeBaseContextProvider>
    </UIContextProvider>
  );
}
