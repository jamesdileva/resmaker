import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { GrammarSuggestions } from './GrammarSuggestions';
import type { PolishSuggestion } from '../api/llm';

const suggestion: PolishSuggestion = {
  original: 'resolving complaints',
  replacement: 'resolving escalations',
  type: 'grammar',
  reason: 'stronger verb phrase',
};

describe('GrammarSuggestions', () => {
  it('shows the diff pair and reason with accept/reject actions', () => {
    const onAccept = vi.fn();
    const onReject = vi.fn();
    render(
      <GrammarSuggestions
        suggestions={[suggestion]}
        onAccept={onAccept}
        onReject={onReject}
      />,
    );
    expect(screen.getByText(suggestion.original)).toBeTruthy();
    expect(screen.getByText(suggestion.replacement)).toBeTruthy();
    expect(screen.getByText(suggestion.reason)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));
    expect(onAccept).toHaveBeenCalledWith(suggestion);
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));
    expect(onReject).toHaveBeenCalledWith(suggestion);
  });

  it('renders an empty state when nothing survives filtering', () => {
    render(
      <GrammarSuggestions suggestions={[]} onAccept={vi.fn()} onReject={vi.fn()} />,
    );
    expect(screen.getByTestId('polish-empty').textContent).toContain(
      'No polish suggestions',
    );
  });
});
