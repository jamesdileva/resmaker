import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render } from '@testing-library/react';
import { UIContextProvider } from '../contexts/UIContext';
import { Settings } from './Settings';
import * as llmApi from '../api/llm';

describe('Settings', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads the current config into the form', async () => {
    vi.spyOn(llmApi, 'getLlmConfig').mockResolvedValue({
      enabled: true,
      endpoint: 'http://127.0.0.1:11434',
      model: 'gemma2',
      max_tokens: 500,
      temperature: 0.3,
    });
    render(<UIContextProvider><Settings /></UIContextProvider>);
    await waitFor(() =>
      expect((screen.getByLabelText(/Enable LLM polish/) as HTMLInputElement).checked).toBe(
        true,
      ),
    );
  });

  it('saves toggled config via the API', async () => {
    vi.spyOn(llmApi, 'getLlmConfig').mockResolvedValue({
      enabled: false,
      endpoint: 'http://127.0.0.1:11434',
      model: 'gemma2',
      max_tokens: 500,
      temperature: 0.3,
    });
    const saveSpy = vi
      .spyOn(llmApi, 'updateLlmConfig')
      .mockResolvedValue({
        enabled: true,
        endpoint: 'http://127.0.0.1:11434',
        model: 'gemma2',
        max_tokens: 500,
        temperature: 0.3,
      });
    render(<UIContextProvider><Settings /></UIContextProvider>);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save settings' })).toBeTruthy());
    fireEvent.click(screen.getByLabelText(/Enable LLM polish/));
    fireEvent.click(screen.getByRole('button', { name: 'Save settings' }));
    await waitFor(() => expect(saveSpy).toHaveBeenCalled());
    expect(saveSpy.mock.calls[0][0].enabled).toBe(true);
  });

  it('surfaces load failures without crashing', async () => {
    vi.spyOn(llmApi, 'getLlmConfig').mockRejectedValue(new Error('backend down'));
    render(<UIContextProvider><Settings /></UIContextProvider>);
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy());
    expect(screen.getByRole('alert').textContent).toContain('backend down');
  });
});
