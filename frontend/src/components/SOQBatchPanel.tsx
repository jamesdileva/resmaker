import { useState } from 'react';
import {
  buildSoqBatch,
  parseSoqQuestions,
} from '../api/soq';
import { useUI } from '../contexts/UIContext';
import type { BuiltDocument } from '../types/resume';

interface SOQBatchPanelProps {
  onBuilt: (document: BuiltDocument) => void;
}

/**
 * Full-SOQ builder (CalCareers style): paste all questions, add the
 * header identity fields, and build one document containing every
 * numbered question with its evidence-backed response.
 */
export function SOQBatchPanel({ onBuilt }: SOQBatchPanelProps) {
  const { toast } = useUI();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [positionTitle, setPositionTitle] = useState('');
  const [rawQuestions, setRawQuestions] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);

  const questions = parseSoqQuestions(rawQuestions);

  const handleBuild = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      toast('Enter your first and last name', 'warning');
      return;
    }
    if (!positionTitle.trim()) {
      toast('Enter the position title', 'warning');
      return;
    }
    if (questions.length === 0) {
      toast('Paste at least one question ending with "?"', 'warning');
      return;
    }
    setIsBuilding(true);
    try {
      const built = await buildSoqBatch({
        questions,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        positionTitle: positionTitle.trim(),
      });
      if (built.warnings.length > 0) {
        toast(built.warnings[0], 'warning');
      }
      onBuilt(built);
      toast(`Full SOQ built (${questions.length} question(s))`, 'success');
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Build failed', 'error');
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div data-testid="soq-batch-panel" style={{ marginTop: 24 }}>
      <h3>Full SOQ (all questions)</h3>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          aria-label="First name"
          placeholder="First name"
          value={firstName}
          onChange={(event) => setFirstName(event.target.value)}
        />
        <input
          aria-label="Last name"
          placeholder="Last name"
          value={lastName}
          onChange={(event) => setLastName(event.target.value)}
        />
        <input
          aria-label="Position title"
          placeholder="Position title"
          value={positionTitle}
          onChange={(event) => setPositionTitle(event.target.value)}
          style={{ minWidth: 200 }}
        />
      </div>
      <textarea
        aria-label="Batch questions"
        placeholder="Paste the SOQ questions here, one per line…"
        value={rawQuestions}
        onChange={(event) => setRawQuestions(event.target.value)}
        rows={6}
        style={{ width: '100%', marginTop: 8 }}
      />
      <p style={{ color: 'var(--text-muted)', margin: '4px 0' }}>
        {questions.length} question(s) detected
      </p>
      <button onClick={() => void handleBuild()} disabled={isBuilding}>
        {isBuilding ? 'Building full SOQ…' : 'Build Full SOQ'}
      </button>
    </div>
  );
}
