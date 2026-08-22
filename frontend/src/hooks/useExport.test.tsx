import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useExport } from './useExport';

const exportApiMock = vi.fn();

vi.mock('../api/build', () => ({
  exportDocument: (...args: unknown[]) => exportApiMock(...args),
}));

function HookHarness({
  onDone,
}: {
  onDone: (filename: string | null) => void;
}) {
  const { exportFile, isExporting } = useExport();
  return (
    <button
      onClick={() => void exportFile('doc-1', { format: 'docx' }).then(onDone)}
      disabled={isExporting}
    >
      go
    </button>
  );
}

describe('useExport', () => {
  beforeEach(() => {
    exportApiMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('downloads the blob and resolves with the filename', async () => {
    // jsdom lacks URL.createObjectURL/revokeObjectURL entirely.
    const createObjectURL = vi.fn(() => 'blob:mock');
    const revokeObjectURL = vi.fn();
    (URL as unknown as Record<string, unknown>).createObjectURL =
      createObjectURL;
    (URL as unknown as Record<string, unknown>).revokeObjectURL =
      revokeObjectURL;
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => {});

    const blob = new Blob(['docx-bytes']);
    exportApiMock.mockResolvedValue({
      blob,
      filename: 'career-os-export.docx',
    });

    const onDone = vi.fn();
    render(<HookHarness onDone={onDone} />);

    fireEvent.click(screen.getByText('go'));

    await waitFor(() => expect(onDone).toHaveBeenCalledWith('career-os-export.docx'));
    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(anchorClick).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock');
  });

  it('resolves null and exposes error on failure', async () => {
    exportApiMock.mockRejectedValue(new Error('Not found'));
    const onDone = vi.fn();
    render(<HookHarness onDone={onDone} />);

    fireEvent.click(screen.getByText('go'));
    await waitFor(() => expect(onDone).toHaveBeenCalledWith(null));
  });
});
