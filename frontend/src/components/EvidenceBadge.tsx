interface EvidenceBadgeProps {
  count: number;
  title?: string;
}

/** Small badge showing how many evidence records back an item. */
export function EvidenceBadge({ count, title }: EvidenceBadgeProps) {
  if (count === 0) {
    return null;
  }
  return (
    <span
      data-testid="evidence-badge"
      title={
        title ?? `Linked to ${count} evidence record${count === 1 ? '' : 's'}`
      }
      style={{
        fontSize: 12,
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: 999,
        padding: '1px 8px',
      }}
    >
      ⛓ {count} evidence
    </span>
  );
}
