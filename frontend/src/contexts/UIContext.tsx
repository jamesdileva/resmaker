import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type ToastKind = 'success' | 'warning' | 'error';

export interface ToastMessage {
  id: number;
  text: string;
  kind: ToastKind;
}

export interface UIContextType {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  toasts: ToastMessage[];
  toast: (message: string, kind?: ToastKind) => void;
  dismissToast: (id: number) => void;
}

const UIContext = createContext<UIContextType | undefined>(undefined);

let nextToastId = 1;

interface ProviderProps {
  children: ReactNode;
}

export function UIContextProvider({ children }: ProviderProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // The stylesheet's dark palette is the :root default; reflecting the
  // state onto <html data-theme> keeps a future light theme a one-file
  // remap away.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((collapsed) => !collapsed);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toastItem) => toastItem.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, kind: ToastKind = 'success') => {
      const id = nextToastId++;
      setToasts((current) => [...current, { id, text: message, kind }]);
      window.setTimeout(() => dismissToast(id), 4000);
    },
    [dismissToast],
  );

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      sidebarCollapsed,
      toggleSidebar,
      toasts,
      toast,
      dismissToast,
    }),
    [theme, sidebarCollapsed, toggleSidebar, toasts, toast, dismissToast],
  );

  return (
    <UIContext.Provider value={value}>
      {children}
      <div role="status" aria-live="polite">
        {toasts.map((entry) => (
          <div
            key={entry.id}
            role={entry.kind === 'error' ? 'alert' : 'status'}
            style={{
              position: 'fixed',
              bottom: 16,
              right: 16,
              padding: '10px 14px',
              borderRadius: 6,
              color: '#fff',
              background:
                entry.kind === 'error'
                  ? '#dc2626'
                  : entry.kind === 'warning'
                    ? '#d97706'
                    : '#16a34a',
              marginBottom: 8,
              maxWidth: 360,
            }}
          >
            {entry.text}
          </div>
        ))}
      </div>
    </UIContext.Provider>
  );
}

export function useUI(): UIContextType {
  const context = useContext(UIContext);
  if (!context) {
    throw new Error('useUI must be used within UIContextProvider');
  }
  return context;
}
