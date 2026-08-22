import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type BuilderKind = 'resume' | 'soq' | 'duty';

export interface BuilderContextType {
  currentBuilder: BuilderKind;
  setCurrentBuilder: (builder: BuilderKind) => void;
  selectedItems: string[];
  addSelectedItem: (id: string) => void;
  removeSelectedItem: (id: string) => void;
  clearSelectedItems: () => void;
}

const BuilderContext = createContext<BuilderContextType | undefined>(undefined);

interface ProviderProps {
  children: ReactNode;
}

export function BuilderContextProvider({ children }: ProviderProps) {
  const [currentBuilder, setCurrentBuilder] = useState<BuilderKind>('resume');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);

  const addSelectedItem = useCallback((id: string) => {
    setSelectedItems((current) =>
      current.includes(id) ? current : [...current, id],
    );
  }, []);

  const removeSelectedItem = useCallback((id: string) => {
    setSelectedItems((current) => current.filter((item) => item !== id));
  }, []);

  const clearSelectedItems = useCallback(() => {
    setSelectedItems([]);
  }, []);

  const value = useMemo(
    () => ({
      currentBuilder,
      setCurrentBuilder,
      selectedItems,
      addSelectedItem,
      removeSelectedItem,
      clearSelectedItems,
    }),
    [currentBuilder, selectedItems, addSelectedItem, removeSelectedItem, clearSelectedItems],
  );

  return (
    <BuilderContext.Provider value={value}>{children}</BuilderContext.Provider>
  );
}

export function useBuilder(): BuilderContextType {
  const context = useContext(BuilderContext);
  if (!context) {
    throw new Error('useBuilder must be used within BuilderContextProvider');
  }
  return context;
}
