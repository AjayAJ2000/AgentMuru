import { describe, expect, it } from 'vitest'

import { serializeCsv } from './csv'

const columns = [{ label: 'Value', key: 'value' }]

describe('serializeCsv', () => {
  it.each(['=1+1', '+cmd', '-2+3', '@SUM(A1)', '\t=1', '\r=1', '  =1'])(
    'neutralizes spreadsheet formula input %j',
    value => {
      const escaped = `'${value}`.split('"').join('""')
      expect(serializeCsv(columns, [{ value }])).toContain(`"${escaped}"`)
    },
  )

  it('quotes headers, commas, quotes, and Unicode with CRLF and a BOM', () => {
    expect(
      serializeCsv(
        [{ label: 'Display, name', key: 'name' }],
        [{ name: 'A "quoted" ✓' }],
      ),
    ).toBe('\uFEFF"Display, name"\r\n"A ""quoted"" ✓"')
  })

  it('preserves ordinary numbers and text', () => {
    expect(serializeCsv(columns, [{ value: 42 }, { value: 'ready' }]))
      .toBe('\uFEFF"Value"\r\n"42"\r\n"ready"')
  })
})
