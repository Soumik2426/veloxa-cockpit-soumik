export interface ReadableEvidence {
  fileName: string;
  location?: string;
  supports?: string;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function readableEvidence(value: unknown): ReadableEvidence[] {
  if (!Array.isArray(value)) return [];

  return value.flatMap((item) => {
    if (typeof item === 'string') {
      return [{ fileName: item }];
    }

    const record = asRecord(item);
    if (!record) return [];

    const reference = asRecord(record.source_reference) ?? record;
    const fileName =
      String(reference.file_name ?? reference.source_file ?? '').trim() ||
      'Source file unavailable';

    const location =
      reference.page !== undefined
        ? `Page ${reference.page}`
        : reference.sheet_name !== undefined
          ? `Sheet ${reference.sheet_name}`
          : reference.sheet !== undefined
            ? `Sheet ${reference.sheet}`
            : reference.section !== undefined
              ? `Section ${reference.section}`
              : undefined;

    const content = record.content;
    const supports =
      typeof content === 'string'
        ? content.replace(/\s+/g, ' ').trim().slice(0, 180)
        : undefined;

    return [{ fileName, location, supports }];
  });
}

export function readableConfidence(value: unknown): string {
  if (typeof value === 'string') return value;
  const record = asRecord(value);
  if (!record) return '';

  const level = String(record.level ?? '').trim();
  const rationale = String(record.rationale ?? '').trim();
  return [level, rationale].filter(Boolean).join(' - ');
}
