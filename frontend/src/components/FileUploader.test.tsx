import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { FileUploader } from './FileUploader';

describe('FileUploader', () => {
  it('accepts a supported file via the file input', () => {
    const onAccepted = vi.fn();
    render(<FileUploader onFileAccepted={onAccepted} />);

    const input = document.querySelector('input[type="file"]')!;
    const file = new File(['data'], 'resume.docx');
    Object.defineProperty(input, 'files', { value: [file] });
    fireEvent.change(input);

    expect(onAccepted).toHaveBeenCalledWith(file);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('rejects unsupported extensions with a visible error', () => {
    const onAccepted = vi.fn();
    render(<FileUploader onFileAccepted={onAccepted} />);

    const input = document.querySelector('input[type="file"]')!;
    const file = new File(['x'], 'sheet.xlsx');
    Object.defineProperty(input, 'files', { value: [file] });
    fireEvent.change(input);

    expect(onAccepted).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/not supported/i);
  });

  it('accepts a dropped file', () => {
    const onAccepted = vi.fn();
    render(<FileUploader onFileAccepted={onAccepted} />);

    const dropZone = screen.getByTestId('drop-zone');
    const file = new File(['x'], 'soq.pdf');
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    expect(onAccepted).toHaveBeenCalledWith(file);
  });

  it('ignores drops when disabled', () => {
    const onAccepted = vi.fn();
    render(<FileUploader onFileAccepted={onAccepted} disabled />);

    const dropZone = screen.getByTestId('drop-zone');
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [new File(['x'], 'resume.txt')] },
    });

    expect(onAccepted).not.toHaveBeenCalled();
  });
});
