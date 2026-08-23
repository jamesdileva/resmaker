import type { ExperienceGroup } from '../types/resume';

interface DutyStatementResponseProps {
  groups: ExperienceGroup[];
  excludedIds: string[];
  onToggleExcluded: (evidenceId: string) => void;
}

/** Shows each duty with its matched evidence; groups can be excluded. */
export function DutyStatementResponse({
  groups,
  excludedIds,
  onToggleExcluded,
}: DutyStatementResponseProps) {
  return (
    <div data-testid="duty-response">
      <h3>Parsed Duties ({groups.length})</h3>
      {groups.length === 0 ? (
        <p style={{ color: 'var(--text-faint)' }}>
          Parse a duty statement to see requirements here.
        </p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {groups.map((group) => {
            const excluded = excludedIds.includes(group.evidence_id);
            return (
              <li
                key={group.evidence_id + group.title}
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  padding: 8,
                  marginBottom: 8,
                  opacity: excluded ? 0.45 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <strong>{group.title}</strong>
                  <button
                    aria-label={`Toggle ${group.title}`}
                    onClick={() => onToggleExcluded(group.evidence_id)}
                  >
                    {excluded ? 'Include' : 'Exclude'}
                  </button>
                </div>
                {group.bullets.map((bullet, index) => (
                  <p
                    key={index}
                    data-traceability={group.evidence_id}
                    style={{ margin: '4px 0 0', fontSize: 13 }}
                  >
                    {bullet.slice(0, 140)}
                    {bullet.length > 140 ? '…' : ''}
                  </p>
                ))}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
