import { useEffect, useRef, useState } from 'react';
import { analyzeQuestion, type SoqAnalysis } from '../api/soq';

interface SOQQuestionInputProps {
  value: string;
  onChange: (question: string) => void;
}

/** Question text area with debounced live category detection. */
export function SOQQuestionInput({ value, onChange }: SOQQuestionInputProps) {
  const [analysis, setAnalysis] = useState<SoqAnalysis | null>(null);
  const latestValue = useRef(value);

  useEffect(() => {
    latestValue.current = value;
    if (value.trim().length < 5) {
      setAnalysis(null);
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        const result = await analyzeQuestion(value.trim());
        if (latestValue.current === value) {
          setAnalysis(result);
        }
      } catch {
        if (latestValue.current === value) {
          setAnalysis(null);
        }
      }
    }, 400);
    return () => window.clearTimeout(timer);
  }, [value]);

  return (
    <div data-testid="soq-question-input">
      <label htmlFor="soq-question">
        <strong>SOQ Question</strong>
      </label>
      <textarea
        id="soq-question"
        rows={3}
        placeholder="Paste the SOQ question here…"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{ width: '100%', marginTop: 4 }}
      />
      {analysis && (
        <p data-testid="category-chip" style={{ margin: '6px 0 0' }}>
          Detected category:{' '}
          <span
            style={{
              background: 'var(--info-bg)',
              border: '1px solid var(--info-border)',
              borderRadius: 999,
              padding: '2px 10px',
            }}
          >
            {analysis.category}
          </span>
        </p>
      )}
    </div>
  );
}
