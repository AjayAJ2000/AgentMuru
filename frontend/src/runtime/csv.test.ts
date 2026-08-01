import { describe, expect, it } from 'vitest'
import { serializeCsv } from './csv'

describe('serializeCsv', () => {
  it.each(['=1+1', '+cmd', '-2+3', '@SUM(A1)', '\t=1', '\r=1', '  =1']) (
    'neutralizes spreadsheet formula %s',
    value => {
      const csv = serializeCsv([{ label: 'Value', key: 'value' }], [{ value }])
      expect(csv).toContain(`"'${value.split('"').join('""')}"`)
    },
  )

  it('quotes headers, quotes, commas, and Unicode with CRLF and BOM', () => {
    expect(serializeCsv(
      [{ label: 'Display, name', key: 'name' }],
      [{ name: 'A "quoted" ✓' }],
    )).toBe('\uFEFF"Display, name"\r\n"A ""quoted"" ✓"')
  })
})
