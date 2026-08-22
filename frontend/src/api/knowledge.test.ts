import { describe, expect, it, vi, beforeEach } from 'vitest';
import {
  listKnowledgeItems,
  getKnowledgeItem,
  searchKnowledgeItems,
} from './knowledge';

vi.mock('./client', () => ({
  API_BASE_URL: 'http://test',
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from './client';

const mockedGet = vi.mocked(apiClient.get);

describe('knowledge API', () => {
  beforeEach(() => {
    mockedGet.mockReset();
  });

  it('listKnowledgeItems returns items and total', async () => {
    const payload = { items: [{ id: 'a' }], total: 1 };
    mockedGet.mockResolvedValue({ data: payload });
    const result = await listKnowledgeItems({ type: 'resume_bullet' });
    expect(result).toEqual(payload);
    expect(mockedGet).toHaveBeenCalledWith('/knowledge-items/', {
      params: { type: 'resume_bullet' },
    });
  });

  it('getKnowledgeItem fetches by id', async () => {
    const item = { id: 'abc' };
    mockedGet.mockResolvedValue({ data: item });
    expect(await getKnowledgeItem('abc')).toEqual(item);
    expect(mockedGet).toHaveBeenCalledWith('/knowledge-items/abc');
  });

  it('searchKnowledgeItems passes query and min_score', async () => {
    mockedGet.mockResolvedValue({ data: [] });
    await searchKnowledgeItems('confidential', 0.5);
    expect(mockedGet).toHaveBeenCalledWith('/knowledge-items/search', {
      params: { q: 'confidential', min_score: 0.5 },
    });
  });
});
