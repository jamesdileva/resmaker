import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useKnowledgeItems } from './useKnowledgeItems';

const listMock = vi.fn();

vi.mock('../api/knowledge', () => ({
  listKnowledgeItems: (...args: unknown[]) => listMock(...args),
}));

describe('useKnowledgeItems', () => {
  beforeEach(() => {
    listMock.mockReset();
  });

  it('loads items with loading state transitions', async () => {
    listMock.mockResolvedValue({
      items: [{ id: 'a' }, { id: 'b' }],
      total: 2,
    });
    const { result } = renderHook(() => useKnowledgeItems());
    expect(result.current.isLoading).toBe(true);
    await waitFor(() => {
      expect(result.current.items).toHaveLength(2);
    });
    expect(result.current.total).toBe(2);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('reports errors and allows refetch', async () => {
    listMock.mockRejectedValueOnce(new Error('Not found'));
    const { result } = renderHook(() => useKnowledgeItems());
    await waitFor(() => {
      expect(result.current.error).toBe('Not found');
    });

    listMock.mockResolvedValue({ items: [], total: 0 });
    await act(async () => {
      await result.current.refetch();
    });
    await waitFor(() => {
      expect(result.current.error).toBeNull();
      expect(result.current.total).toBe(0);
    });
  });
});
