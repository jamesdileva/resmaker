import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { SectionOrganizer, orderedSections } from './SectionOrganizer';
import type { BuiltDocument } from '../types/resume';

const SECTIONS = [
  {
    title: 'Summary',
    section_type: 'profile',
    profile_lines: ['John Doe'],
    groups: [],
    lines: [],
  },
  {
    title: 'Experience',
    section_type: 'experience',
    profile_lines: [],
    groups: [
      { evidence_id: 'ev1', title: 'Job', dates: null, bullets: ['Did a thing'] },
    ],
    lines: [],
  },
  {
    title: 'Skills',
    section_type: 'skills',
    profile_lines: [],
    groups: [],
    lines: ['Excel'],
  },
];

const DOCUMENT = {
  document_id: 'doc-1',
  template_name: 'standard',
  sections: SECTIONS,
  traceability: {},
  warnings: [],
} satisfies BuiltDocument;

describe('SectionOrganizer', () => {
  it('renders sections in the given order', () => {
    render(
      <SectionOrganizer
        sections={SECTIONS}
        order={['profile', 'experience', 'skills']}
        onOrderChange={vi.fn()}
      />,
    );
    const items = screen.getAllByText(/☰/);
    expect(items).toHaveLength(3);
  });

  it('reorders a dragged section before its drop target', () => {
    const onOrderChange = vi.fn();
    render(
      <SectionOrganizer
        sections={SECTIONS}
        order={['profile', 'experience', 'skills']}
        onOrderChange={onOrderChange}
      />,
    );

    const experience = screen.getByTestId('section-handle-experience');
    const skills = screen.getByTestId('section-handle-skills');
    fireEvent.dragStart(experience);
    fireEvent.drop(skills);

    expect(onOrderChange).toHaveBeenCalledWith([
      'profile',
      'skills',
      'experience',
    ]);
  });

  it('ignores drops when nothing is being dragged', () => {
    const onOrderChange = vi.fn();
    render(
      <SectionOrganizer
        sections={SECTIONS}
        order={['profile', 'experience', 'skills']}
        onOrderChange={onOrderChange}
      />,
    );
    fireEvent.drop(screen.getByTestId('section-handle-profile'));
    expect(onOrderChange).not.toHaveBeenCalled();
  });
});

describe('orderedSections', () => {
  it('orders document sections by the organizer order', () => {
    const result = orderedSections(DOCUMENT, ['skills', 'profile', 'experience']);
    expect(result.map((s) => s.section_type)).toEqual([
      'skills',
      'profile',
      'experience',
    ]);
  });

  it('appends sections missing from the order list', () => {
    const result = orderedSections(DOCUMENT, ['experience']);
    expect(result.map((s) => s.section_type)).toEqual(['experience', 'profile', 'skills']);
  });
});
