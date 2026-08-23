// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SOQBatchPanel } from './SOQBatchPanel';
import * as soqApi from '../api/soq';
import type { BuiltDocument } from '../types/resume';

vi.mock('../api/soq', () => ({
  buildSoqBatch: vi.fn(),
  parseSoqQuestions: vi.fn((raw: string) =>
    raw
      .split(/\r?\n/)
      .map((line: string) => line.replace(/^\s*(?:\(?\d+[.)]|[a-z][.)])\s*/i, '').trim())
      .filter((line: string) => line.endsWith('?')),
  ),
}));

vi.mock('../contexts/UIContext', () => ({
  useUI: () => ({ toast: vi.fn() }),
}));

const builtDoc = {
  document_id: 'doc-1',
  template_name: 'soq_standard_batch',
  sections: [],
  traceability: {},
  warnings: [],
  metadata: {},
} as unknown as BuiltDocument;

const PASTED = [
  'Statement of Qualifications - intro boilerplate:',
  '1. Describe your experience prioritizing assignments?',
  '2) Describe your experience with confidential records?',
].join('\n');

function fillForm() {
  fireEvent.change(screen.getByLabelText('First name'), {
    target: { value: 'James' },
  });
  fireEvent.change(screen.getByLabelText('Last name'), {
    target: { value: 'Dileva' },
  });
  fireEvent.change(screen.getByLabelText('Position title'), {
    target: { value: 'Claims Analyst' },
  });
  fireEvent.change(screen.getByLabelText('Batch questions'), {
    target: { value: PASTED },
  });
}

describe('SOQBatchPanel', () => {
  it('detects numbered questions and strips the boilerplate', () => {
    render(<SOQBatchPanel onBuilt={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Batch questions'), {
      target: { value: PASTED },
    });
    expect(screen.getByText('2 question(s) detected')).toBeTruthy();
  });

  it('builds a full SOQ with header fields', async () => {
    const mock = vi.mocked(soqApi.buildSoqBatch).mockResolvedValue(builtDoc);
    const onBuilt = vi.fn();
    render(<SOQBatchPanel onBuilt={onBuilt} />);
    fillForm();
    fireEvent.click(screen.getByRole('button', { name: 'Build Full SOQ' }));
    await waitFor(() => expect(onBuilt).toHaveBeenCalledWith(builtDoc));
    const payload = mock.mock.calls[0][0];
    expect(payload.questions).toHaveLength(2);
    expect(payload.firstName).toBe('James');
    expect(payload.positionTitle).toBe('Claims Analyst');
  });

  it('refuses to build without identity fields or questions', async () => {
    const mock = vi.mocked(soqApi.buildSoqBatch).mockResolvedValue(builtDoc);
    render(<SOQBatchPanel onBuilt={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Build Full SOQ' }));
    await waitFor(() => expect(mock).not.toHaveBeenCalled());
  });
});
