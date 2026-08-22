import { useEffect, useRef } from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  debounceMs?: number;
  disabled?: boolean;
}

/** Text input that propagates changes after a debounce delay. */
export function SearchBar({
  value,
  onChange,
  debounceMs = 300,
  disabled,
}: SearchBarProps) {
  const latestValue = useRef(value);

  useEffect(() => {
    if (value === latestValue.current) {
      return;
    }
    const timer = window.setTimeout(() => {
      latestValue.current = value;
      onChange(value);
    }, debounceMs);
    return () => window.clearTimeout(timer);
  }, [value, onChange, debounceMs]);

  return (
    <input
      data-testid="explorer-search-bar"
      aria-label="Search knowledge base"
      placeholder="Search your evidence…"
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      style={{ width: '100%', padding: '8px 10px' }}
    />
  );
}
