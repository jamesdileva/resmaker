import { useEffect, useState } from 'react';
import {
  getLlmConfig,
  updateLlmConfig,
  type LLMConfig,
} from '../api/llm';
import { useUI } from '../contexts/UIContext';

const DEFAULT_FORM: LLMConfig = {
  enabled: false,
  endpoint: 'http://127.0.0.1:11434',
  model: 'gemma2',
  max_tokens: 500,
  temperature: 0.3,
};

export function Settings() {
  const { toast } = useUI();
  const [config, setConfig] = useState<LLMConfig>(DEFAULT_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getLlmConfig()
      .then((loaded) => {
        if (!cancelled) setConfig(loaded);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load settings');
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const saved = await updateLlmConfig(config);
      setConfig(saved);
      toast(
        saved.enabled
          ? `LLM polish enabled (${saved.model})`
          : 'LLM polish disabled',
        'success',
      );
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Save failed', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div>
        <h2>Settings</h2>
        <p data-testid="settings-loading" style={{ color: 'var(--text-faint)' }}>
          Loading…
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2>Settings</h2>
      <section style={{ maxWidth: 480 }}>
        <h3>Local LLM Polish (Ollama)</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
          Optional. When enabled, a local Ollama model may suggest grammar and
          transition improvements as diffs — it can never change your facts,
          and nothing is applied until you accept.
        </p>
        {error && (
          <p role="alert" style={{ color: '#dc2626' }}>
            {error}
          </p>
        )}
        <label style={{ display: 'block', margin: '12px 0' }}>
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(event) =>
              setConfig({ ...config, enabled: event.target.checked })
            }
          />{' '}
          Enable LLM polish
        </label>
        <label style={{ display: 'block', margin: '12px 0', color: 'var(--text-muted)' }}>
          Endpoint
          <input
            type="text"
            value={config.endpoint}
            onChange={(event) =>
              setConfig({ ...config, endpoint: event.target.value })
            }
            style={{ display: 'block', width: '100%', marginTop: 4 }}
          />
        </label>
        <label style={{ display: 'block', margin: '12px 0', color: 'var(--text-muted)' }}>
          Model
          <input
            type="text"
            value={config.model}
            onChange={(event) => setConfig({ ...config, model: event.target.value })}
            style={{ display: 'block', width: '100%', marginTop: 4 }}
          />
        </label>
        <button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Saving…' : 'Save settings'}
        </button>
      </section>
    </div>
  );
}
