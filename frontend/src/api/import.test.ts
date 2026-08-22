import { describe, expect, it, vi } from 'vitest';
import {
  getFileExtension,
  pollImportStatus,
} from './import';

vi.mock('./client', () => ({
  API_BASE_URL: 'http://test',
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('import helpers', () => {
  it('extracts lowercase extensions', () => {
    expect(getFileExtension('Resume.DOCX')).toBe('docx');
    expect(getFileExtension('no-extension')).toBe('');
  });

  it('pollImportStatus stops on terminal states', async () => {
    const { apiClient } = await import('./client');
    const mockedGet = vi.mocked(apiClient.get);
    mockedGet.mockResolvedValue({
      data: { job_id: 'IMP-1', status: 'completed', items_created: 4 },
    });

    const result = await pollImportStatus('IMP-1', { intervalMs: 1 });
    expect(result.status).toBe('completed');
    expect(mockedGet).toHaveBeenCalledTimes(1);
  });
});
