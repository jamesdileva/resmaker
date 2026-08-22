import { describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { BuilderContextProvider, useBuilder } from './BuilderContext';

describe('BuilderContext', () => {
  it('starts with resume builder and empty selection', () => {
    const { result } = renderHook(() => useBuilder(), {
      wrapper: BuilderContextProvider,
    });
    expect(result.current.currentBuilder).toBe('resume');
    expect(result.current.selectedItems).toEqual([]);
  });

  it('adds and removes selected items without duplicates', () => {
    const { result } = renderHook(() => useBuilder(), {
      wrapper: BuilderContextProvider,
    });
    act(() => result.current.addSelectedItem('a'));
    act(() => result.current.addSelectedItem('a'));
    act(() => result.current.addSelectedItem('b'));
    expect(result.current.selectedItems).toEqual(['a', 'b']);
    act(() => result.current.removeSelectedItem('a'));
    expect(result.current.selectedItems).toEqual(['b']);
    act(() => result.current.clearSelectedItems());
    expect(result.current.selectedItems).toEqual([]);
  });

  it('switches the active builder kind', () => {
    const { result } = renderHook(() => useBuilder(), {
      wrapper: BuilderContextProvider,
    });
    act(() => result.current.setCurrentBuilder('soq'));
    expect(result.current.currentBuilder).toBe('soq');
  });

  it('throws outside the provider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useBuilder())).toThrow();
  });
});
