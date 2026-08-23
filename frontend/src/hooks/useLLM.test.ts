import { describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useLLM } from './useLLM';
import * as llmApi from '../api/llm';
import type { PolishableItem } from './useLLM';

vi.mock('../api/llm', () => ({
  polishText: vi.fn(),
}));

const items: PolishableItem[] = [
  { id: 'a', content: 'Processed over 50 records while resolving complaints.' },
  { id: 'b', content: 'Drafted correspondence for management review.' },
];

describe('useLLM', () => {
  it('polishes combined text and exposes suggestions', async () => {
    vi.mocked(llmApi.polishText).mockResolvedValue([
      { original: 'resolving complaints', replacement: 'resolving escalations', type: 'grammar', reason: '' },
    ]);
    const { result } = renderHook(() => useLLM());
    await act(async () => {
      await result.current.polish(items);
    });
    expect(result.current.suggestions).toHaveLength(1);
    // the item contents were joined so a single request covers them all
    expect(vi.mocked(llmApi.polishText).mock.calls[0][0]).toContain('Drafted correspondence');
  });

  it('applySuggestion rewrites only the owning item', async () => {
    vi.mocked(llmApi.polishText).mockResolvedValue([]);
    const { result } = renderHook(() => useLLM());
    const suggestion = {
      original: 'resolving complaints',
      replacement: 'resolving escalations',
      type: 'grammar',
      reason: '',
    };
    let updates: Record<string, string> = {};
    act(() => {
      updates = result.current.applySuggestion(suggestion, items);
    });
    expect(updates['a']).toBe('Processed over 50 records while resolving escalations.');
    expect(updates['b']).toBeUndefined();
    expect(result.current.suggestions).toHaveLength(0);
  });

  it('surfaces API errors as error state', async () => {
    vi.mocked(llmApi.polishText).mockRejectedValue(new Error('Ollama unreachable'));
    const { result } = renderHook(() => useLLM());
    await act(async () => {
      await result.current.polish(items);
    });
    await waitFor(() => expect(result.current.error).toContain('Ollama unreachable'));
  });
});
