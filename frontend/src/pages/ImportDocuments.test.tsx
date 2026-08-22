import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ImportDocuments } from './ImportDocuments';
import { UIContextProvider } from '../contexts/UIContext';

const uploadMock = vi.fn();
const pollMock = vi.fn();

vi.mock('../api/import', () => ({
  SUPPORTED_IMPORT_TYPES: ['docx', 'pdf', 'txt'],
  getFileExtension: (name: string) => name.split('.').pop()?.toLowerCase() ?? '',
  uploadDocument: (...args: unknown[]) => uploadMock(...args),
  pollImportStatus: (...args: unknown[]) => pollMock(...args),
}));

function renderPage() {
  return render(
    <UIContextProvider>
      <ImportDocuments />
    </UIContextProvider>,
  );
}

describe('ImportDocuments', () => {
  beforeEach(() => {
    uploadMock.mockReset();
    pollMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('shows empty history initially', () => {
    renderPage();
    expect(screen.getByText(/No imports yet/)).toBeInTheDocument();
  });

  it('records a completed import in history', async () => {
    uploadMock.mockResolvedValue({
      job_id: 'IMP-1',
      status: 'completed',
      items_created: 8,
    });

    const { container } = renderPage();
    const fileInput = container.querySelector('input[type="file"]')!;
    Object.defineProperty(fileInput, 'files', {
      value: [new File(['x'], 'resume.pdf')],
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByTestId('import-history')).toHaveTextContent(
        /resume\.pdf.*8 items created/,
      );
    });
    expect(pollMock).not.toHaveBeenCalled();
  });

  it('polls when the server reports processing', async () => {
    uploadMock.mockResolvedValue({ job_id: 'IMP-2', status: 'processing' });
    pollMock.mockResolvedValue({
      job_id: 'IMP-2',
      status: 'completed',
      items_created: 3,
    });

    const { container } = renderPage();
    const fileInput = container.querySelector('input[type="file"]')!;
    Object.defineProperty(fileInput, 'files', {
      value: [new File(['x'], 'soq.docx')],
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(pollMock).toHaveBeenCalledWith('IMP-2');
      expect(screen.getByTestId('import-history')).toHaveTextContent(
        /3 items created/,
      );
    });
  });

  it('surfaces failed imports', async () => {
    uploadMock.mockRejectedValue(new Error('Not found'));

    const { container } = renderPage();
    const fileInput = container.querySelector('input[type="file"]')!;
    Object.defineProperty(fileInput, 'files', {
      value: [new File(['x'], 'resume.pdf')],
    });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText(/No imports yet|failed/i)).toBeInTheDocument();
    });
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
