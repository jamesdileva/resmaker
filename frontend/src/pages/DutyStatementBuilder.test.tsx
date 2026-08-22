import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { DutyStatementBuilder } from './DutyStatementBuilder';
import { BuilderContextProvider } from '../contexts/BuilderContext';
import { UIContextProvider } from '../contexts/UIContext';

const previewMock = vi.fn();
const buildMock = vi.fn();
const suggestMock = vi.fn();

vi.mock('../api/duty', () => ({
  previewDuties: (...args: unknown[]) => previewMock(...args),
  buildDutyResponse: (...args: unknown[]) => buildMock(...args),
}));

vi.mock('../api/build', () => ({
  suggestEvidence: (...args: unknown[]) => suggestMock(...args),
}));

function renderPage() {
  return render(
    <UIContextProvider>
      <BuilderContextProvider>
        <DutyStatementBuilder />
      </BuilderContextProvider>
    </UIContextProvider>,
  );
}

const DUTIES = [
  {
    text: 'Resolve customer complaints and disputes daily.',
    order_index: 0,
    category: 'Customer Service',
    keywords: ['resolve', 'customer'],
  },
];

const SUGGESTION = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content: 'Resolved 20+ customer complaints daily',
    category: 'Customer Service',
  },
  score: 0.9,
  evidence_id: 'ev-1',
};

const BUILT_DOC = {
  document_id: 'doc-1',
  template_name: 'duty_standard',
  sections: [
    {
      title: 'Duty Statement Responses',
      section_type: 'duty_response',
      profile_lines: [],
      groups: [
        {
          evidence_id: 'ev-1',
          title: 'Duty 1: Resolve customer complaints and disputes daily.',
          dates: null,
          bullets: ['Resolved 20+ customer complaints daily'],
        },
      ],
      lines: [],
    },
  ],
  traceability: { 'item-1': 'ev-1' },
  warnings: [],
  metadata: {},
};

describe('DutyStatementBuilder page', () => {
  beforeEach(() => {
    previewMock.mockReset();
    buildMock.mockReset();
    suggestMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('parses pasted text and lists duties', async () => {
    previewMock.mockResolvedValue(DUTIES);
    renderPage();

    fireEvent.change(screen.getByLabelText(/Job Posting \/ Duty Statement/i), {
      target: { value: '1. Resolve customer complaints daily.' },
    });
    fireEvent.click(screen.getByText('Parse Duties'));

    await waitFor(() => {
      expect(previewMock).toHaveBeenCalledWith(
        '1. Resolve customer complaints daily.',
      );
    });
  });

  it('adds evidence and builds a response into the preview', async () => {
    previewMock.mockResolvedValue(DUTIES);
    suggestMock.mockResolvedValue([SUGGESTION]);
    buildMock.mockResolvedValue(BUILT_DOC);

    renderPage();

    fireEvent.change(screen.getByLabelText(/Job Posting \/ Duty Statement/i), {
      target: { value: '1. Resolve customer complaints daily.' },
    });
    fireEvent.click(screen.getByText('Parse Duties'));
    await waitFor(() => expect(previewMock).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'complaints' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));

    fireEvent.click(screen.getByText('Build Response'));
    await waitFor(() => {
      expect(screen.getByTestId('document-preview')).toBeInTheDocument();
    });
    const preview = screen.getByTestId('document-preview');
    expect(preview).toHaveTextContent('Resolved 20+ customer complaints daily');
    expect(buildMock).toHaveBeenCalledWith({
      rawText: '1. Resolve customer complaints daily.',
      selectedItemIds: ['item-1'],
    });
  });

  it('warns when building without parsed duties or evidence', async () => {
    renderPage();
    fireEvent.click(screen.getByText('Build Response'));
    expect(await screen.findByText(/Parse a duty statement first/i)).toBeInTheDocument();
    expect(buildMock).not.toHaveBeenCalled();
  });

  it('disables export until the export pipeline exists', () => {
    renderPage();
    expect(screen.getByText('Export')).toBeDisabled();
  });
});
