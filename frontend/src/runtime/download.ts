export type DownloadLink = {
  href: string
  download: string
  click: () => void
}

export type CsvDownloadEnvironment = {
  createBlob: (csv: string) => unknown
  createObjectUrl: (blob: unknown) => string
  createLink: () => DownloadLink
  appendLink: (link: DownloadLink) => void
  removeLink: (link: DownloadLink) => void
  revokeObjectUrl: (url: string) => void
  defer: (callback: () => void) => void
}

export function triggerCsvDownload(
  csv: string,
  filename: string,
  environment: CsvDownloadEnvironment,
): void {
  const blob = environment.createBlob(csv)
  const url = environment.createObjectUrl(blob)
  const link = environment.createLink()
  link.href = url
  link.download = filename
  environment.appendLink(link)
  try {
    link.click()
  } finally {
    environment.removeLink(link)
    environment.defer(() => environment.revokeObjectUrl(url))
  }
}

export function browserCsvDownloadEnvironment(): CsvDownloadEnvironment {
  return {
    createBlob: (csv) => new Blob([csv], { type: 'text/csv;charset=utf-8;' }),
    createObjectUrl: (blob) => URL.createObjectURL(blob as Blob),
    createLink: () => document.createElement('a'),
    appendLink: (link) => document.body.appendChild(link as HTMLAnchorElement),
    removeLink: (link) => (link as HTMLAnchorElement).remove(),
    revokeObjectUrl: (url) => URL.revokeObjectURL(url),
    defer: (callback) => window.setTimeout(callback, 0),
  }
}
