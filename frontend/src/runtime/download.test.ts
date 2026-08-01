import { describe, expect, it } from 'vitest'

import { triggerCsvDownload, type CsvDownloadEnvironment } from './download'

describe('triggerCsvDownload', () => {
  it('clicks an attached link and defers object URL revocation', () => {
    const events: string[] = []
    let deferred: (() => void) | undefined
    const link = {
      href: '',
      download: '',
      click: () => events.push('click'),
    }
    const environment: CsvDownloadEnvironment = {
      createBlob: () => {
        events.push('blob')
        return {}
      },
      createObjectUrl: () => {
        events.push('url')
        return 'blob:export'
      },
      createLink: () => {
        events.push('link')
        return link
      },
      appendLink: () => events.push('append'),
      removeLink: () => events.push('remove'),
      revokeObjectUrl: () => events.push('revoke'),
      defer: (callback) => {
        events.push('defer')
        deferred = callback
      },
    }

    triggerCsvDownload('account,mrr\r\nAcme,100', 'accounts.csv', environment)

    expect(link.href).toBe('blob:export')
    expect(link.download).toBe('accounts.csv')
    expect(events).toEqual(['blob', 'url', 'link', 'append', 'click', 'remove', 'defer'])
    deferred?.()
    expect(events[events.length - 1]).toBe('revoke')
  })
})
