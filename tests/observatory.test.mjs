import test from 'node:test';
import assert from 'node:assert/strict';
import { parseManifest } from '../observatory.mjs';

function fixture() {
  const keys = ['lunar_objectives', 'mars_objectives', 'technology_gaps', 'data_gaps'];
  return { generated_at: '2026-01-01T00:00:00Z', revision: 'C', document_id: '123',
    normalized_counts: { lunar_objective_rows: 10, mars_objective_rows: 10, technology_gaps: 10, data_gaps: 3 },
    sources: Object.fromEntries(keys.map(key => [key, { filename: key + '.xlsx',
      url: 'https://www.nasa.gov/wp-content/uploads/' + key + '.xlsx', sha256: 'a'.repeat(64),
      bytes: 100, record_count: 10 }])) };
}

test('preserves raw versus normalized data-gap counts', () => {
  const result = parseManifest(fixture());
  assert.equal(result.sources.length, 4);
  assert.equal(result.sources[3].rawCount, 10);
  assert.equal(result.sources[3].count, 3);
});
for (const [name, mutate] of [
  ['missing required source', x => delete x.sources.technology_gaps],
  ['malformed hash', x => x.sources.technology_gaps.sha256 = 'invalid'],
  ['external source host', x => x.sources.technology_gaps.url = 'https://nasa.gov.attacker.example/wp-content/uploads/technology_gaps.xlsx'],
  ['credential-bearing URL', x => x.sources.technology_gaps.url = 'https://user@www.nasa.gov/wp-content/uploads/technology_gaps.xlsx'],
  ['insecure source URL', x => x.sources.technology_gaps.url = 'http://www.nasa.gov/wp-content/uploads/technology_gaps.xlsx'],
  ['wrong source filename', x => x.sources.technology_gaps.url = 'https://www.nasa.gov/wp-content/uploads/other.xlsx'],
  ['string count', x => x.normalized_counts.technology_gaps = '10'],
  ['inconsistent raw count', x => x.normalized_counts.technology_gaps = 9],
  ['normalized data gaps exceed raw rows', x => x.normalized_counts.data_gaps = 11],
  ['invalid timestamp', x => x.generated_at = 'not a date'],
  ['unexpected revision', x => x.revision = 'D']
]) test('rejects ' + name, () => { const x = fixture(); mutate(x); assert.throws(() => parseManifest(x)); });
