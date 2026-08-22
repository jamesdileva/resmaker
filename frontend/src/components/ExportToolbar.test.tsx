import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ExportToolbar } from './ExportToolbar';
import { ExportDialog } from './ExportDialog';
import { UIContextProvider } from '../contexts/UIContext';

const exportFileMock = vi.fn();

vi.mock('../hooks/useExport', () => ({
  useExport: () => ({
    exportFile: (...args: unknown[]) => exportFileMock(...args),
    isExporting: false,
    error: null,
  }),
}));

function UIWrap({ children }: { children: ReactNode }) {
  return <UIContextProvider>{children}</UIContextProvider>;
}

describe('ExportDialog', () => {
  it('renders nothing when closed', () => {
    render(<ExportDialog open={false} onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.queryByTestId('export-dialog')).toBeNull();
  });

  it('defaults to docx with traceability on, and submits the selection', () => {
    const onConfirm = vi.fn();
    render(<ExportDialog open onConfirm={onConfirm} onCancel={vi.fn()} />);

    expect(screen.getByRole('radio', { name: /DOCX/ })).toBeChecked();
    expect(screen.getByTestId('traceability-toggle')).toBeChecked();
    expect(screen.getByText(/PDF \(coming soon\)/)).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('TXT (plain text)'));
    fireEvent.click(screen.getByTestId('traceability-toggle'));
    fireEvent.click(screen.getByTestId('confirm-export'));

    expect(onConfirm).toHaveBeenCalledWith('txt', false);
  });

  it('cancels without confirming', () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<ExportDialog open onConfirm={onConfirm} onCancel={onCancel} />);

    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe('ExportToolbar', () => {
  beforeEach(() => {
    exportFileMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('disables export when no document has been built', () => {
    render(
      <UIWrap>
        <ExportToolbar documentId={null} />
      </UIWrap>,
    );
    expect(screen.getByTestId('open-export')).toBeDisabled();
    expect(screen.getByText('PDF')).toBeDisabled();
  });

  it('opens dialog and exports with the chosen options', async () => {
    exportFileMock.mockResolvedValue('career-os-export.docx');
    render(
      <UIWrap>
        <ExportToolbar documentId="doc-1" />
      </UIWrap>,
    );

    fireEvent.click(screen.getByTestId('open-export'));
    fireEvent.click(screen.getByTestId('confirm-export'));

    await waitFor(() => {
      expect(exportFileMock).toHaveBeenCalledWith(
        'doc-1',
        expect.objectContaining({ format: 'docx', includeTraceability: true }),
      );
    });
  });

  it('reports failed exports as errors', async () => {
    // The hook contract: failures resolve to null (never reject).
    exportFileMock.mockResolvedValue(null);
    render(
      <UIWrap>
        <ExportToolbar documentId="doc-1" />
      </UIWrap>,
    );

    fireEvent.click(screen.getByTestId('open-export'));
    fireEvent.click(screen.getByTestId('confirm-export'));
    expect(await screen.findByText('Export failed')).toBeInTheDocument();
  });
});
