import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { SOQQuestionInput } from './SOQQuestionInput';

const analyzeMock = vi.fn();

vi.mock('../api/soq', () => ({
  analyzeQuestion: (...args: unknown[]) => analyzeMock(...args),
  countWords: (text: string) => (text.trim() ? text.trim().split(/\s+/).length : 0),
}));

describe('SOQQuestionInput', () => {
  it('renders the question textarea', () => {
    render(<SOQQuestionInput value="" onChange={vi.fn()} />);
    expect(screen.getByLabelText(/SOQ Question/i)).toBeInTheDocument();
  });

  it('propagates edits', () => {
    const onChange = vi.fn();
    render(<SOQQuestionInput value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/SOQ Question/i), {
      target: { value: 'Describe your experience' },
    });
    expect(onChange).toHaveBeenCalledWith('Describe your experience');
  });

  it('detects and displays the category after debounce', async () => {
    vi.useFakeTimers();
    analyzeMock.mockResolvedValue({
      category: 'Confidential Information',
      keywords: ['confidential'],
    });
    const question = 'Describe how you handled confidential information';
    const { rerender } = render(
      <SOQQuestionInput value="" onChange={vi.fn()} />,
    );

    rerender(<SOQQuestionInput value={question} onChange={vi.fn()} />);
    await vi.advanceTimersByTimeAsync(500);

    expect(analyzeMock).toHaveBeenCalledWith(question);
    expect(screen.getByTestId('category-chip')).toHaveTextContent(
      'Confidential Information',
    );
    vi.useRealTimers();
  });

  it('hides the category chip for short input', () => {
    render(<SOQQuestionInput value="ab" onChange={vi.fn()} />);
    expect(screen.queryByTestId('category-chip')).toBeNull();
  });
});
