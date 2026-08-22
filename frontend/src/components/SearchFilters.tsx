import { useState } from 'react';
import type { SearchFiltersState } from '../api/search';

const ITEM_TYPES = [
  { value: 'resume_bullet', label: 'Resume bullets' },
  { value: 'soq_paragraph', label: 'SOQ paragraphs' },
];

interface SearchFiltersProps {
  filters: SearchFiltersState;
  onChange: (filters: SearchFiltersState) => void;
}

export function SearchFilters({ filters, onChange }: SearchFiltersProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div data-testid="search-filters">
      <button
        aria-expanded={!collapsed}
        onClick={() => setCollapsed((c) => !c)}
        style={{ width: '100%', textAlign: 'left' }}
      >
        {collapsed ? '▸ Filters' : '▾ Filters'}
      </button>
      {!collapsed && (
        <div style={{ marginTop: 8 }}>
          <fieldset style={{ border: 'none', padding: 0, margin: '0 0 10px' }}>
            <legend>
              <strong>Item type</strong>
            </legend>
            {ITEM_TYPES.map(({ value, label }) => (
              <label key={value} style={{ display: 'block' }}>
                <input
                  type="checkbox"
                  checked={filters.itemTypes.includes(value)}
                  onChange={() =>
                    onChange({
                      ...filters,
                      itemTypes: filters.itemTypes.includes(value)
                        ? filters.itemTypes.filter((t) => t !== value)
                        : [...filters.itemTypes, value],
                    })
                  }
                />{' '}
                {label}
              </label>
            ))}
          </fieldset>

          <p style={{ margin: '0 0 4px' }}>
            <strong>Category</strong>
          </p>
          <input
            aria-label="Category filter"
            placeholder="e.g. Analysis"
            value={filters.categories[0] ?? ''}
            onChange={(event) =>
              onChange({
                ...filters,
                categories: event.target.value
                  ? [event.target.value.trim()]
                  : [],
              })
            }
            style={{ width: '100%', marginBottom: 10 }}
          />

          <p style={{ margin: '0 0 4px' }}>
            <strong>Min star rating</strong>
          </p>
          <select
            aria-label="Minimum star rating"
            value={filters.minStarRating}
            onChange={(event) =>
              onChange({
                ...filters,
                minStarRating: Number(event.target.value),
              })
            }
            style={{ width: '100%', marginBottom: 10 }}
          >
            {[0, 1, 2, 3, 4, 5].map((stars) => (
              <option key={stars} value={stars}>
                {stars === 0 ? 'Any' : `${stars}+ stars`}
              </option>
            ))}
          </select>

          <p style={{ margin: '0 0 4px' }}>
            <strong>Sort by</strong>
          </p>
          <select
            aria-label="Sort results by"
            value={filters.sortBy}
            onChange={(event) =>
              onChange({
                ...filters,
                sortBy: event.target.value as SearchFiltersState['sortBy'],
              })
            }
            style={{ width: '100%' }}
          >
            <option value="relevance">Relevance</option>
            <option value="date">Date (newest)</option>
          </select>
        </div>
      )}
    </div>
  );
}
