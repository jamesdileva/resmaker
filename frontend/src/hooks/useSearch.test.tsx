import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSearch } from './useSearch';

const searchMock = vi.fn();

vi.mock('../api/knowledge', () => ({
  searchKnowledgeItems: (...args: unknown[]) => searchMock(...args),
}));

describe('useSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    searchMock.mockReset();
  });

  it('returns no results for empty query without calling the API', async () => {
    const { result } = renderHook(() => useSearch('   '));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(result.current.results).toEqual([]);
    expect(result.current.isSearching).toBe(false);
    expect(searchMock).not.toHaveBeenCalled();
  });

  it('debounces and returns ranked results', async () => {
    searchMock.mockResolvedValue([{ knowledge_item: { id: '1' }, score: 0.9 }]);
    const { result, rerender } = renderHook(({ q }) => useSearch(q), {
      initialProps: { q: '' },
    });

    rerender({ q: 'confidential' });
    expect(searchMock).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });

    expect(searchMock).toHaveBeenCalledWith('confidential', 0.3);
    expect(result.current.results).toHaveLength(1);
    expect(result.current.isSearching).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('surfaces API errors', async () => {
    searchMock.mockRejectedValue(new Error('Request failed'));
    const { result } = renderHook(() => useSearch('boom'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });
    expect(result.current.error).toBe('Request failed');
    expect(result.current.results).toEqual([]);
  });
});
