export interface CsvColumn {
  label: unknown
  key: string
}

const DANGEROUS_SPREADSHEET_VALUE = /^(?:[\t\r]|\s*[=+\-@])/

function quoteField(value: unknown, neutralizeFormula: boolean): string {
  let text = String(value ?? '')
  if (neutralizeFormula && DANGEROUS_SPREADSHEET_VALUE.test(text)) {
    text = `'${text}`
  }
  return `"${text.split('"').join('""')}"`
}

export function serializeCsv(
  columns: CsvColumn[],
  rows: Array<Record<string, unknown>>,
): string {
  const header = columns.map(column => quoteField(column.label, false)).join(',')
  const body = rows.map(row => (
    columns.map(column => quoteField(row[column.key], true)).join(',')
  ))
  return `\uFEFF${[header, ...body].join('\r\n')}`
}
