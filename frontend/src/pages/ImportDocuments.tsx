import { useCallback, useState } from 'react';
import { FileUploader } from '../components/FileUploader';
import {
  ProgressTracker,
  type ProgressPhase,
} from '../components/ProgressTracker';
import { pollImportStatus, uploadDocument } from '../api/import';
import { useUI } from '../contexts/UIContext';

interface ImportHistoryEntry {
  jobId: string;
  filename: string;
  status: 'completed' | 'failed';
  itemsCreated?: number;
  error?: string | null;
}

export function ImportDocuments() {
  const [phase, setPhase] = useState<ProgressPhase>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [history, setHistory] = useState<ImportHistoryEntry[]>([]);
  const { toast } = useUI();

  const handleFileAccepted = useCallback(
    async (file: File) => {
      setUploadProgress(0);
      setPhase('uploading');
      try {
        const submitted = await uploadDocument(file, {
          onUploadProgress: setUploadProgress,
        });
        setPhase('processing');

        const final =
          submitted.status === 'processing'
            ? await pollImportStatus(submitted.job_id)
            : submitted;

        if (final.status === 'completed') {
          setPhase('done');
          setHistory((current) => [
            {
              jobId: final.job_id,
              filename: file.name,
              status: 'completed',
              itemsCreated: final.items_created ?? 0,
            },
            ...current,
          ]);
          toast(
            `Imported ${file.name}: ${final.items_created ?? 0} items created`,
            'success',
          );
        } else {
          setPhase('error');
          setHistory((current) => [
            {
              jobId: final.job_id,
              filename: file.name,
              status: 'failed',
              error: final.error,
            },
            ...current,
          ]);
          toast(final.error ?? 'Import failed', 'error');
        }
      } catch (err) {
        setPhase('error');
        toast(err instanceof Error ? err.message : 'Import failed', 'error');
      }
    },
    [toast],
  );

  return (
    <section>
      <h2>Import Documents</h2>
      <p>
        Upload existing resumes and SOQs to build your knowledge base.
      </p>

      <FileUploader onFileAccepted={handleFileAccepted} disabled={phase === 'uploading' || phase === 'processing'} />
      <ProgressTracker phase={phase} progress={uploadProgress} />

      <h3>Import History</h3>
      {history.length === 0 ? (
        <p style={{ color: '#6b7280' }}>No imports yet this session.</p>
      ) : (
        <ul data-testid="import-history">
          {history.map((entry) => (
            <li key={entry.jobId}>
              <strong>{entry.filename}</strong>{' '}
              {entry.status === 'completed'
                ? `- ${entry.itemsCreated} items created`
                : `- failed: ${entry.error ?? 'unknown error'}`}{' '}
              <span style={{ color: '#9ca3af' }}>({entry.jobId})</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
