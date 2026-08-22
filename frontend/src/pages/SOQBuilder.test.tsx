import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SOQBuilder } from './SOQBuilder';
import { BuilderContextProvider } from '../contexts/BuilderContext';
import { UIContextProvider } from '../contexts/UIContext';

const analyzeMock = vi.fn();
const suggestMock = vi.fn();
const answerMock = vi.fn();

vi.mock('../api/soq', () => ({
  analyzeQuestion: (...args: unknown[]) => analyzeMock(...args),
  answerSoq: (...args: unknown[]) => answerMock(...args),
  countWords: (text: string) => (text.trim() ? text.trim().split(/\s+/).length : 0),
}));

vi.mock('../api/build', () => ({
  suggestEvidence: (...args: unknown[]) => suggestMock(...args),
}));

function renderPage() {
  return render(
    <UIContextProvider>
      <BuilderContextProvider>
        <SOQBuilder />
      </BuilderContextProvider>
    </UIContextProvider>,
  );
}

const SUGGESTION = {
  knowledge_item: {
    id: 'soq-item-1',
    type: 'soq_paragraph',
    title: null,
    content: 'I managed confidential customer records and verified identities.',
    category: 'Confidential Information',
  },
  score: 0.9,
  evidence_id: 'ev-1',
};

describe('SOQBuilder page', () => {
  beforeEach(() => {
    analyzeMock.mockReset();
    suggestMock.mockReset();
    answerMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('adds evidence and builds a response shown in preview', async () => {
    analyzeMock.mockResolvedValue({ category: 'General', keywords: [] });
    suggestMock.mockResolvedValue([SUGGESTION]);
    answerMock.mockResolvedValue({
      document_id: 'doc-1',
      template_name: 'soq_standard',
      sections: [
        {
          title: 'Question',
          section_type: 'soq_question',
          profile_lines: ['Describe your experience'],
          groups: [],
          lines: [],
        },
        {
          title: 'Response',
          section_type: 'soq_response',
          profile_lines: [],
          groups: [],
          lines: [SUGGESTION.knowledge_item.content],
        },
      ],
      traceability: { 'soq-item-1': 'ev-1' },
      warnings: [],
      metadata: { category: 'Confidential Information' },
    });

    renderPage();

    fireEvent.change(screen.getByLabelText(/SOQ Question/i), {
      target: { value: 'Describe your experience handling confidential information' },
    });
    await waitFor(() => expect(analyzeMock).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'confidential' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));

    fireEvent.click(screen.getByText('Build Response'));
    await waitFor(() => {
      const preview = screen.getByTestId('document-preview');
      expect(preview).toHaveTextContent('Describe your experience');
      expect(preview).toHaveTextContent(/verified identities/);
    });
    expect(answerMock).toHaveBeenCalledWith(
      'Describe your experience handling confidential information',
      ['soq-item-1'],
      250,
    );
  });

  it('warns when building without a question or evidence', async () => {
    renderPage();
    fireEvent.click(screen.getByText('Build Response'));
    expect(await screen.findByText(/Enter the SOQ question first/i)).toBeInTheDocument();
    expect(answerMock).not.toHaveBeenCalled();
  });

  it('surfaces build failures as error toasts', async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/SOQ Question/i), {
      target: { value: 'Valid question here' },
    });
    // Inject selection directly through the editor path is complex; simulate
    // by mocking a rejected call after manually selecting via suggestion flow.
    suggestMock.mockResolvedValue([SUGGESTION]);
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'x' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));

    answerMock.mockRejectedValue(new Error('No valid knowledge items selected'));
    fireEvent.click(screen.getByText('Build Response'));

    const alerts = await screen.findAllByRole('alert');
    expect(alerts.some((el) => el.textContent?.includes('No valid'))).toBe(true);
  });

  it('disables export until the export pipeline exists', () => {
    renderPage();
    expect(screen.getByText('Export')).toBeDisabled();
  });
});
