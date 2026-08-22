import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { SOQEditor } from './SOQEditor';

const ITEMS = [
  { id: 'a', content: 'one two three four five' },
  { id: 'b', content: 'six seven eight nine ten eleven twelve' },
];

describe('SOQEditor', () => {
  it('shows the running word count against the limit', () => {
    render(<SOQEditor items={ITEMS} maxWords={250} onRemove={vi.fn()} onClear={vi.fn()} />);
    expect(screen.getByTestId('word-count')).toHaveTextContent('12 / 250 words');
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '5',
    );
  });

  it('flags when over the word limit', () => {
    render(<SOQEditor items={ITEMS} maxWords={10} onRemove={vi.fn()} onClear={vi.fn()} />);
    expect(screen.getByTestId('word-count')).toHaveTextContent('over limit');
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '100',
    );
  });

  it('removes individual items and clears all', () => {
    const onRemove = vi.fn();
    const onClear = vi.fn();
    render(<SOQEditor items={ITEMS} onRemove={onRemove} onClear={onClear} />);

    fireEvent.click(screen.getByLabelText('Remove a'));
    expect(onRemove).toHaveBeenCalledWith('a');

    fireEvent.click(screen.getByLabelText('Clear evidence selection'));
    expect(onClear).toHaveBeenCalled();
  });

  it('shows an empty hint with no items', () => {
    render(<SOQEditor items={[]} onRemove={vi.fn()} onClear={vi.fn()} />);
    expect(screen.getByText(/Add evidence suggestions/i)).toBeInTheDocument();
  });
});
