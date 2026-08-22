import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { EvidenceBadge } from './EvidenceBadge';
import { ProvenancePanel } from './ProvenancePanel';

const provenanceMock = vi.fn();

vi.mock('../api/knowledge', () => ({
  getKnowledgeProvenance: (...args: unknown[]) => provenanceMock(...args),
}));

describe('EvidenceBadge', () => {
  it('renders nothing with zero evidence', () => {
    render(<EvidenceBadge count={0} />);
    expect(screen.queryByTestId('evidence-badge')).toBeNull();
  });

  it('shows the evidence count', () => {
    render(<EvidenceBadge count={2} />);
    expect(screen.getByTestId('evidence-badge')).toHaveTextContent(
      /2 evidence/,
    );
  });
});

const PROVENANCE = {
  knowledge_item: {
    id: 'item-1',
    type: 'resume_bullet',
    title: null,
    content: 'Handled confidential customer records daily',
    category: null,
    confidence: null,
    metadata_json: {},
    source_doc_id: 'doc-1',
    created_at: '2026-08-22T00:00:00Z',
    updated_at: '2026-08-22T00:00:00Z',
  },
  source_document: {
    id: 'doc-1',
    filename: 'resume.pdf',
    file_type: 'pdf',
    imported_at: '2026-08-22T00:00:00Z',
  },
  evidence: [
    {
      id: 'ev-1',
      title: 'Boost Mobile',
      type: 'experience',
      company: 'Boost Mobile',
      role: 'Sales Associate',
      strength: 4,
      success_rate: 1.0,
    },
  ],
  usage: [
    {
      application_id: 'app-1',
      applied_at: '2026-07-01T00:00:00Z',
      application_status: 'offer',
      result: 'offer',
      used_in_resume: true,
      used_in_soq: false,
      used_in_duty: false,
    },
  ],
};

describe('ProvenancePanel', () => {
  beforeEach(() => {
    provenanceMock.mockReset();
  });

  it('loads and renders all provenance sections', async () => {
    provenanceMock.mockResolvedValue(PROVENANCE);
    render(<ProvenancePanel itemId="item-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId('provenance-item')).toHaveTextContent(
        /confidential customer records/,
      );
    });
    expect(screen.getByTestId('provenance-source')).toHaveTextContent(
      'resume.pdf',
    );
    expect(screen.getByTestId('provenance-evidence')).toHaveTextContent(
      'Boost Mobile',
    );
    expect(screen.getByTestId('provenance-usage')).toHaveTextContent('offer');
  });

  it('closes via the close button', async () => {
    provenanceMock.mockResolvedValue(PROVENANCE);
    const onClose = vi.fn();
    render(<ProvenancePanel itemId="item-1" onClose={onClose} />);

    await screen.findByTestId('provenance-item');
    fireEvent.click(screen.getByLabelText('Close provenance panel'));
    expect(onClose).toHaveBeenCalled();
  });

  it('shows empty hints when no source or usage exists', async () => {
    provenanceMock.mockResolvedValue({
      ...PROVENANCE,
      source_document: null,
      usage: [],
      evidence: [],
    });
    render(<ProvenancePanel itemId="item-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/No source document recorded/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/No linked evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Not yet used in any application/i)).toBeInTheDocument();
  });

  it('surfaces load errors', async () => {
    provenanceMock.mockRejectedValue(new Error('Not found'));
    render(<ProvenancePanel itemId="missing" onClose={vi.fn()} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Not found');
  });
});
