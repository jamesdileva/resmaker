import { useState } from 'react';

interface DutyStatementInputProps {
  onParse: (rawText: string) => void;
  disabled?: boolean;
}

export function DutyStatementInput({ onParse, disabled }: DutyStatementInputProps) {
  const [text, setText] = useState('');

  return (
    <div data-testid="duty-input">
      <label htmlFor="duty-text">
        <strong>Job Posting / Duty Statement</strong>
      </label>
      <textarea
        id="duty-text"
        rows={10}
        placeholder="Paste the duty statement from the job posting here…"
        value={text}
        onChange={(event) => setText(event.target.value)}
        style={{ width: '100%', marginTop: 4 }}
      />
      <button
        onClick={() => onParse(text)}
        disabled={disabled || text.trim().length === 0}
        style={{ marginTop: 8 }}
      >
        {disabled ? 'Parsing…' : 'Parse Duties'}
      </button>
    </div>
  );
}
