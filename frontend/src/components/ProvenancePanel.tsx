import { useEffect, useState } from 'react';
import {
  getKnowledgeProvenance,
  type ProvenanceData,
} from '../api/knowledge';
import { StarRating } from './StarRating';
import { EvidenceBadge } from './EvidenceBadge';

interface ProvenancePanelProps {
  itemId: string;
  onClose: () => void;
}

/** Side panel showing full trace info for one knowledge item. */
export function ProvenancePanel({ itemId, onClose }: ProvenancePanelProps) {
  const [data, setData] = useState<ProvenanceData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    setData(null);
    getKnowledgeProvenance(itemId)
      .then((result) => {
        if (!cancelled) {
          setData(result);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [itemId]);

  return (
    <div
      data-testid="provenance-panel"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 420,
        height: '100vh',
        overflowY: 'auto',
        background: 'var(--panel)',
        borderLeft: '2px solid var(--border)',
        boxShadow: '-4px 0 12px rgba(0,0,0,0.08)',
        padding: 20,
        zIndex: 50,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>Provenance</h3>
        <button aria-label="Close provenance panel" onClick={onClose}>
          ✕
        </button>
      </div>

      {isLoading && <p>Loading…</p>}
      {error && (
        <p role="alert" style={{ color: '#dc2626' }}>
          {error}
        </p>
      )}

      {data && (
        <>
          <section style={{ marginTop: 12 }}>
            <h4>Item</h4>
            <p data-testid="provenance-item">
              [{data.knowledge_item.type}]{' '}
              {data.knowledge_item.content.slice(0, 160)}
            </p>
          </section>

          <section style={{ marginTop: 12 }}>
            <h4>Source Document</h4>
            {data.source_document ? (
              <p data-testid="provenance-source">
                📄 {data.source_document.filename}{' '}
                <small>({data.source_document.file_type})</small>
              </p>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No source document recorded.</p>
            )}
          </section>

          <section style={{ marginTop: 12 }}>
            <h4>Linked Evidence ({data.evidence.length})</h4>
            {data.evidence.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No linked evidence.</p>
            ) : (
              data.evidence.map((record) => (
                <div key={record.id} data-testid="provenance-evidence" style={{ marginBottom: 8 }}>
                  <strong>{record.title}</strong>{' '}
                  <small>
                    ({record.role ?? record.type}
                    {record.company ? ` · ${record.company}` : ''})
                  </small>
                  <div>
                    Strength {record.strength}/5 · historical success{' '}
                    <StarRating rating={Math.round(record.success_rate * 5)} />
                    <EvidenceBadge count={1} title={record.title} />
                  </div>
                </div>
              ))
            )}
          </section>

          <section style={{ marginTop: 12 }}>
            <h4>Usage History ({data.usage.length})</h4>
            {data.usage.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>Not yet used in any application.</p>
            ) : (
              data.usage.map((entry) => (
                <div key={entry.application_id} data-testid="provenance-usage" style={{ marginBottom: 8 }}>
                  Application{' '}
                  <small>({entry.applied_at.slice(0, 10)})</small> — status:{' '}
                  <strong>{entry.application_status}</strong>
                  {entry.result && (
                    <>
                      {' '}
                      · outcome:{' '}
                      <span
                        style={{
                          color:
                            entry.result === 'rejected' ? '#dc2626' : '#16a34a',
                        }}
                      >
                        {entry.result === 'interview' && '🎤 '}
                        {entry.result === 'offer' && '🎉 '}
                        {entry.result}
                      </span>
                    </>
                  )}
                </div>
              ))
            )}
          </section>
        </>
      )}
    </div>
  );
}
