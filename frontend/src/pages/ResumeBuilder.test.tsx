import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ResumeBuilder } from './ResumeBuilder';
import {
  BuilderContextProvider,
} from '../contexts/BuilderContext';
import { UIContextProvider } from '../contexts/UIContext';

const suggestMock = vi.fn();
const buildMock = vi.fn();

vi.mock('../api/build', () => ({
  suggestEvidence: (...args: unknown[]) => suggestMock(...args),
  buildResume: (...args: unknown[]) => buildMock(...args),
}));

function renderPage() {
  return render(
    <UIContextProvider>
      <BuilderContextProvider>
        <ResumeBuilder />
      </BuilderContextProvider>
    </UIContextProvider>,
  );
}

const SUGGESTION = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content: 'Handled confidential records daily',
    category: null,
  },
  score: 0.9,
  evidence_id: 'ev-1',
};

describe('ResumeBuilder', () => {
  beforeEach(() => {
    suggestMock.mockReset();
    buildMock.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('adds a suggestion to the selection and builds a resume', async () => {
    suggestMock.mockResolvedValue([SUGGESTION]);
    buildMock.mockResolvedValue({
      document_id: 'doc-1',
      template_name: 'standard',
      sections: [
        {
          title: 'Experience',
          section_type: 'experience',
          profile_lines: [],
          groups: [
            {
              evidence_id: 'ev-1',
              title: 'Job',
              dates: null,
              bullets: ['Handled confidential records daily'],
            },
          ],
          lines: [],
        },
      ],
      traceability: { 'item-1': 'ev-1' },
      warnings: [],
    });

    renderPage();

    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'confidential' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));

    expect(screen.getByTestId('content-editor')).toHaveTextContent(
      /Selected Evidence \(1\)/,
    );

    fireEvent.click(screen.getByText('Build Resume'));
    await waitFor(() => {
      expect(screen.getByTestId('document-preview')).toBeInTheDocument();
    });
    const preview = screen.getByTestId('document-preview');
    expect(preview).toHaveTextContent('Handled confidential records daily');
    expect(preview).toHaveTextContent('Experience');
    expect(buildMock).toHaveBeenCalledWith(['item-1']);
  });

  it('warns when building with an empty selection', async () => {
    renderPage();
    fireEvent.click(screen.getByText('Build Resume'));

    expect(
      await screen.findByText(/Select at least one evidence item first/i),
    ).toBeInTheDocument();
    expect(buildMock).not.toHaveBeenCalled();
  });

  it('surfaces build failures as error toasts', async () => {
    suggestMock.mockResolvedValue([SUGGESTION]);
    buildMock.mockRejectedValue(new Error('No valid knowledge items selected'));

    renderPage();
    fireEvent.change(screen.getByLabelText('Search query'), {
      target: { value: 'x' },
    });
    fireEvent.click(screen.getByText('Suggest'));
    await waitFor(() => screen.getByTestId('suggestion-item'));
    fireEvent.click(screen.getByText('Add'));
    fireEvent.click(screen.getByText('Build Resume'));

    const alerts = await screen.findAllByRole('alert');
    expect(
      alerts.some((el) =>
        el.textContent?.includes('No valid knowledge items'),
      ),
    ).toBe(true);
  });

  it('disables export until the export pipeline exists', () => {
    renderPage();
    expect(screen.getByText('Export')).toBeDisabled();
  });
});
