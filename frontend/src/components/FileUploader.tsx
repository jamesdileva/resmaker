import { useCallback, useRef, useState, type DragEvent } from 'react';
import { SUPPORTED_IMPORT_TYPES, getFileExtension } from '../api/import';

interface FileUploaderProps {
  onFileAccepted: (file: File) => void;
  disabled?: boolean;
}

export function FileUploader({ onFileAccepted, disabled }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const acceptAttribute = SUPPORTED_IMPORT_TYPES.map((t) => `.${t}`).join(',');

  const validateAndAccept = useCallback(
    (file: File | undefined) => {
      if (!file) {
        return;
      }
      const extension = getFileExtension(file.name);
      if (
        !SUPPORTED_IMPORT_TYPES.includes(
          extension as (typeof SUPPORTED_IMPORT_TYPES)[number],
        )
      ) {
        setValidationError(
          `"${file.name}" is not supported. Allowed types: ${SUPPORTED_IMPORT_TYPES.join(', ')}`,
        );
        return;
      }
      setValidationError(null);
      onFileAccepted(file);
    },
    [onFileAccepted],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (disabled) {
        return;
      }
      const file = event.dataTransfer.files?.[0];
      validateAndAccept(file);
    },
    [disabled, validateAndAccept],
  );

  const handleDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  return (
    <div>
      <div
        data-testid="drop-zone"
        role="button"
        aria-disabled={disabled}
        onClick={() => !disabled && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setIsDragging(false)}
        style={{
          border: `2px dashed ${isDragging ? '#2563eb' : 'var(--border)'}`,
          borderRadius: 8,
          padding: 32,
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          background: isDragging ? 'var(--info-bg)' : 'transparent',
          opacity: disabled ? 0.5 : 1,
        }}
      >
        <p style={{ margin: 0 }}>
          Drag & drop a resume or SOQ here, or click to browse
        </p>
        <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--text-faint)' }}>
          Supported formats: {acceptAttribute}
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={acceptAttribute}
        hidden
        onChange={(event) => {
          validateAndAccept(event.target.files?.[0]);
          event.target.value = '';
        }}
      />
      {validationError && (
        <p role="alert" style={{ color: '#dc2626', fontSize: 14 }}>
          {validationError}
        </p>
      )}
    </div>
  );
}
