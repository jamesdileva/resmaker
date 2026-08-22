import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentPreview } from './DocumentPreview';
import type { BuiltDocument } from '../types/resume';

const DOCUMENT: BuiltDocument = {
  document_id: 'doc-abcdef',
  template_name: 'standard',
  sections: [
    {
      title: 'Summary',
      section_type: 'profile',
      profile_lines: ['John Doe', 'john@example.com'],
      groups: [],
      lines: [],
    },
    {
      title: 'Experience',
      section_type: 'experience',
      profile_lines: [],
      groups: [
        {
          evidence_id: 'ev-1',
          title: 'Sales Associate',
          dates: '2019 - 2022',
          bullets: ['Bullet one', 'Bullet two'],
        },
      ],
      lines: [],
    },
    {
      title: 'Skills',
      section_type: 'skills',
      profile_lines: [],
      groups: [],
      lines: ['Excel', 'SQL'],
    },
  ],
  traceability: { item1: 'ev-1' },
  warnings: [],
};

describe('DocumentPreview', () => {
  it('shows a placeholder when no document exists', () => {
    render(<DocumentPreview document={null} order={[]} />);
    expect(screen.getByTestId('document-preview-empty')).toBeInTheDocument();
  });

  it('renders all sections with headings and content', () => {
    render(<DocumentPreview document={DOCUMENT} order={['profile', 'experience', 'skills']} />);

    expect(screen.getByText('Summary')).toBeInTheDocument();
    expect(screen.getByText('Experience')).toBeInTheDocument();
    expect(screen.getByText('Skills')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText(/Sales Associate/)).toBeInTheDocument();
    expect(screen.getByText('Bullet one')).toBeInTheDocument();
    expect(screen.getByText('• Excel')).toBeInTheDocument();
  });

  it('attaches traceability attributes to bullets', () => {
    render(<DocumentPreview document={DOCUMENT} order={['experience']} />);
    const bullet = screen.getByText('Bullet one');
    expect(bullet).toHaveAttribute('data-traceability', 'ev-1');
  });

  it('respects custom section ordering', () => {
    const { container } = render(
      <DocumentPreview document={DOCUMENT} order={['skills', 'profile', 'experience']} />,
    );
    const headings = Array.from(
      container.querySelectorAll('h3'),
    ).map((h) => h.textContent);
    expect(headings.indexOf('Skills')).toBeLessThan(headings.indexOf('Summary'));
    expect(headings.indexOf('Summary')).toBeLessThan(headings.indexOf('Experience'));
  });
});
