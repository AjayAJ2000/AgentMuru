export type CsvColumn = {
  label: unknown
  key: string
}

const SPREADSHEET_FORMULA_PREFIX = /^(?:[=+\-@\t\r]|[ \f\v]+[=+\-@\t\r])/

function encodeCell(value: unknown): string {
  const raw = String(value ?? '')
  const safe = SPREADSHEET_FORMULA_PREFIX.test(raw) ? `'${raw}` : raw
  return `"${safe.split('"').join('""')}"`
}

export function serializeCsv(
  columns: CsvColumn[],
  rows: Record<string, unknown>[],
): string {
  const header = columns.map(column => encodeCell(column.label)).join(',')
  const body = rows.map(row => (
    columns.map(column => encodeCell(row[column.key])).join(',')
  ))
  return `\uFEFF${[header, ...body].join('\r\n')}`
}
