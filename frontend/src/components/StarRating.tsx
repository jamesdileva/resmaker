interface StarRatingProps {
  rating: number;
}

/** Read-only 1-5 star display with match-quality coloring. */
export function StarRating({ rating }: StarRatingProps) {
  const clamped = Math.max(0, Math.min(5, Math.round(rating)));
  const color =
    clamped >= 4 ? '#16a34a' : clamped === 3 ? '#d97706' : clamped > 0 ? '#6b7280' : 'var(--border)';
  return (
    <span data-testid="star-rating" style={{ color }} title={`${clamped} of 5`}>
      {'★'.repeat(clamped)}
      <span style={{ color: 'var(--border)' }}>{'☆'.repeat(5 - clamped)}</span>
    </span>
  );
}
