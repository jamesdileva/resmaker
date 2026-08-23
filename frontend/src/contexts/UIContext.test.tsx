import { describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { UIContextProvider, useUI } from './UIContext';

describe('UIContext', () => {
  it('defaults to dark theme, reflects data-theme, toggles sidebar', () => {
    const { result } = renderHook(() => useUI(), {
      wrapper: UIContextProvider,
    });
    expect(result.current.theme).toBe('dark');
    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(result.current.sidebarCollapsed).toBe(false);
    act(() => result.current.toggleSidebar());
    expect(result.current.sidebarCollapsed).toBe(true);
    act(() => result.current.setTheme('light'));
    expect(result.current.theme).toBe('light');
    expect(document.documentElement.dataset.theme).toBe('light');
  });

  it('adds and dismisses toasts', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useUI(), {
      wrapper: UIContextProvider,
    });
    act(() => result.current.toast('Saved', 'success'));
    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].text).toBe('Saved');

    const id = result.current.toasts[0].id;
    act(() => result.current.dismissToast(id));
    expect(result.current.toasts).toHaveLength(0);
    vi.useRealTimers();
  });

  it('auto-dismisses toasts after timeout', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useUI(), {
      wrapper: UIContextProvider,
    });
    act(() => result.current.toast('Oops', 'error'));
    expect(result.current.toasts).toHaveLength(1);
    act(() => {
      vi.advanceTimersByTime(4100);
    });
    expect(result.current.toasts).toHaveLength(0);
    vi.useRealTimers();
  });

  it('throws outside the provider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useUI())).toThrow();
  });
});
