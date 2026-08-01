import React, { startTransition, useState, useEffect, useCallback, useRef } from 'react'
import { Renderer } from './Renderer'
import type { VNodeData, ServerMessage } from './types'
import { PatchApplicationError, applyPatches } from './runtime/applyPatch'
import { navigationAction, type NavigationSource } from './runtime/navigation'
import { createReconnectController } from './runtime/reconnect'
import { safeMediaUrl } from './runtime/media'

type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

type LoadingBootstrap = {
  title?: string
  message?: string
  subtitle?: string
  reconnectingMessage?: string
  errorMessage?: string
  animation?: string
  textOnly?: boolean
  asset?: string | null
  assetKind?: 'image' | 'video' | null
  video?: string | null
  themeMode?: 'light' | 'dark'
  modes?: Partial<Record<'light' | 'dark', Partial<LoadingBootstrap>>>
  stylePreset?: 'modern' | 'executive' | 'bento' | 'cyberpunk' | 'minimal'
}

declare global {
  interface Window {
    __BRICKFLOW_BOOTSTRAP__?: LoadingBootstrap
  }
}

function readLoadingBootstrap(): LoadingBootstrap {
  const dataElement = document.getElementById('brickflow-bootstrap')
  if (dataElement?.textContent) {
    try {
      return JSON.parse(dataElement.textContent) as LoadingBootstrap
    } catch (error) {
      console.error('[BrickflowUI] Invalid bootstrap configuration', error)
    }
  }
  return window.__BRICKFLOW_BOOTSTRAP__ || {}
}

const LOADING_BOOTSTRAP: LoadingBootstrap = readLoadingBootstrap()

function resolveLoadingConfig(mode: 'light' | 'dark'): LoadingBootstrap {
  const modeOverrides = LOADING_BOOTSTRAP.modes?.[mode] || {}
  return {
    ...LOADING_BOOTSTRAP,
    ...modeOverrides,
  }
}

function BuiltinLoadingMark() {
  return (
    <div className="bf-loading-mark" aria-hidden="true">
      <div className="bf-loading-mark-tile">
        <span className="bf-loading-mark-bar bf-loading-mark-bar-long" />
        <span className="bf-loading-mark-bar bf-loading-mark-bar-medium" />
        <span className="bf-loading-mark-bar bf-loading-mark-bar-short" />
      </div>
    </div>
  )
}

function SafeText({ className, text }: { className: string; text: string }) {
  const writeText = useCallback((element: HTMLDivElement | null) => {
    if (element) element.textContent = text
  }, [text])

  return <div className={className} ref={writeText} />
}

function LoadingVisual({ status, themeMode }: { status: WsStatus; themeMode: 'light' | 'dark' }) {
  const config = resolveLoadingConfig(themeMode)
  const videoAsset = safeMediaUrl(config.video, window.location.href)
  const configuredAsset = safeMediaUrl(config.asset, window.location.href)
  const asset = videoAsset || configuredAsset
  const kind = videoAsset ? 'video' : config.assetKind
  const animation = config.animation || 'spinner'
  const title = config.title || 'BrickflowUI'
  const subtitle = config.subtitle
  const message =
    status === 'connecting'
      ? (config.message || 'Connecting to runtime...')
      : status === 'disconnected'
        ? (config.reconnectingMessage || 'Reconnecting...')
        : status === 'error'
          ? (config.errorMessage || 'Connection error - retrying...')
          : 'Loading...'

  return (
    <div className={`bf-loading-screen bf-loading-${animation}`}>
      {!config.textOnly ? (
        kind === 'video' && asset ? (
          <video
            className="bf-loading-media"
            src={asset}
            autoPlay
            muted
            loop
            playsInline
          />
        ) : asset ? (
          <img className="bf-loading-media" src={asset} alt="Loading indicator" />
        ) : (
          <BuiltinLoadingMark />
        )
      ) : null}
      <SafeText className="bf-loading-brand" text={title} />
      {subtitle ? <SafeText className="bf-loading-subtitle" text={subtitle} /> : null}
      <SafeText className="bf-loading-hint" text={message} />
    </div>
  )
}

function resolveInitialThemeMode(): 'light' | 'dark' {
  const bootstrapMode = LOADING_BOOTSTRAP.themeMode === 'dark' ? 'dark' : 'light'
  try {
    const stored = window.localStorage.getItem('brickflowui.theme')
    return stored === 'light' || stored === 'dark' ? stored : bootstrapMode
  } catch {
    return bootstrapMode
  }
}

function resolveInitialStylePreset(): string {
  return LOADING_BOOTSTRAP.stylePreset || 'modern'
}

export default function App() {
  const [vdom, setVdom] = useState<VNodeData | null>(null)
  const [status, setStatus] = useState<WsStatus>('connecting')
  const [error, setError] = useState<string | null>(null)
  const [pendingEvents, setPendingEvents] = useState<Map<string, number>>(new Map())
  const [themeMode, setThemeModeState] = useState<'light' | 'dark'>(resolveInitialThemeMode)
  const [stylePreset] = useState<string>(resolveInitialStylePreset)
  const wsRef = useRef<WebSocket | null>(null)
  const vdomRef = useRef<VNodeData | null>(null)
  const frameRef = useRef<number | null>(null)
  const queuedTreeRef = useRef<VNodeData | null>(null)
  const flushQueuedTree = useCallback(() => {
    frameRef.current = null
    const nextTree = queuedTreeRef.current
    if (!nextTree) return
    queuedTreeRef.current = null
    startTransition(() => {
      setVdom(nextTree)
    })
  }, [])

  const scheduleTreeCommit = useCallback((nextTree: VNodeData) => {
    queuedTreeRef.current = nextTree
    if (frameRef.current !== null) return
    frameRef.current = window.requestAnimationFrame(flushQueuedTree)
  }, [flushQueuedTree])

  const dispatch = useCallback((event_id: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setPendingEvents((prev) => {
        const next = new Map(prev)
        next.set(event_id, (next.get(event_id) || 0) + 1)
        return next
      })
      wsRef.current.send(JSON.stringify({ type: 'event', event_id, data }))
    }
  }, [])

  const setThemeMode = useCallback((mode: 'light' | 'dark') => {
    setThemeModeState(mode)
    document.documentElement.dataset.themeMode = mode
    try {
      window.localStorage.setItem('brickflowui.theme', mode)
    } catch {
      // Ignore storage issues in locked-down runtimes.
    }
  }, [])

  const navigateTo = useCallback((path: string, source: NavigationSource) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const action = navigationAction(path, source)
      wsRef.current.send(JSON.stringify(action.message))
      if (action.history === 'push') window.history.pushState({}, '', path)
    }
  }, [])

  const navigate = useCallback((path: string) => navigateTo(path, 'user'), [navigateTo])

  useEffect(() => {
    document.documentElement.dataset.themeMode = themeMode
  }, [themeMode])

  useEffect(() => {
    document.documentElement.dataset.uiPreset = stylePreset
  }, [stylePreset])

  useEffect(() => {
    function connect() {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${location.host}/events?path=${encodeURIComponent(window.location.pathname)}`)
      wsRef.current = ws
      setStatus('connecting')

      ws.onopen = () => {
        reconnectController.opened()
        setStatus('connected')
        setError(null)
      }

      ws.onmessage = (e: MessageEvent) => {
        try {
          const msg: ServerMessage = JSON.parse(e.data as string)

          if (msg.type === 'full') {
            vdomRef.current = msg.tree
            scheduleTreeCommit(msg.tree)
          } else if (msg.type === 'patch') {
            if (vdomRef.current) {
              try {
                const updated = applyPatches(vdomRef.current, msg.patches)
                vdomRef.current = updated
                scheduleTreeCommit({ ...updated })
              } catch (patchError) {
                const message = patchError instanceof PatchApplicationError
                  ? patchError.message
                  : 'Unknown patch application failure'
                console.error('[BrickflowUI] Invalid server patch', patchError)
                setError(`Invalid server patch: ${message}. Reconnecting for a full render.`)
                ws.close()
              }
            }
          } else if (msg.type === 'event_complete') {
            setPendingEvents((prev) => {
              const current = prev.get(msg.event_id)
              if (!current) return prev
              const next = new Map(prev)
              if (current <= 1) next.delete(msg.event_id)
              else next.set(msg.event_id, current - 1)
              return next
            })
          } else if (msg.type === 'error') {
            setError(msg.message)
          }
        } catch (err) {
          console.error('[BrickflowUI] Failed to parse server message', err)
        }
      }

      ws.onclose = () => {
        setStatus('disconnected')
        setPendingEvents(new Map())
        reconnectController.closed()
      }

      ws.onerror = () => {
        setStatus('error')
        setPendingEvents(new Map())
        ws.close()
      }
    }

    const reconnectController = createReconnectController(connect)
    connect()

    const handlePopstate = () => navigateTo(
      `${window.location.pathname}${window.location.search}${window.location.hash}`,
      'popstate',
    )
    window.addEventListener('popstate', handlePopstate)

    return () => {
      reconnectController.dispose()
      if (frameRef.current !== null) {
        window.cancelAnimationFrame(frameRef.current)
      }
      wsRef.current?.close()
      window.removeEventListener('popstate', handlePopstate)
    }
  }, [navigateTo, scheduleTreeCommit])

  if (!vdom) {
    return <LoadingVisual status={status} themeMode={themeMode} />
  }

  return (
    <>
      <div className="bf-page-shell">
        <Renderer
          node={vdom}
          dispatch={dispatch}
          navigate={navigate}
          pendingEvents={pendingEvents}
          themeMode={themeMode}
          setThemeMode={setThemeMode}
        />
      </div>
      {status === 'disconnected' && (
        <div className="bf-connection-banner">Reconnecting to server...</div>
      )}
      {error && (
        <div className="bf-connection-banner" style={{ borderColor: 'var(--db-error)', color: 'var(--db-error)', background: 'var(--db-error-bg)' }}>
          Runtime error: {error}
        </div>
      )}
    </>
  )
}
