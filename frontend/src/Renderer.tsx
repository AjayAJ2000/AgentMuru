import React, { useCallback, useEffect, useId, useRef, useState } from 'react'
import * as LucideIcons from 'lucide-react'
import type { VNodeData } from './types'
import { shouldSubmitChatInput } from './runtime/chat'
import { serializeCsv } from './runtime/csv'
import {
  CatalogBrowserView,
  JobTriggerView,
  WarehouseSelectorView,
} from './runtime/databricksComponents'
import {
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  ScatterChart as ReScatterChart, Scatter,
  ComposedChart as ReComposedChart,
  RadarChart as ReRadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  FunnelChart as ReFunnelChart, Funnel,
  Treemap,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts'

// ── Lucide icon lookup ────────────────────────────────────────────────────
// We only load icons used by the navigation system; others render as text
const LUCIDE_ICON_MAP: Record<string, string> = {
  Home: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10',
  Database: 'M12 2C6.48 2 2 4.24 2 7s4.48 5 10 5 10-2.24 10-5S17.52 2 12 2zM2 17c0 2.76 4.48 5 10 5s10-2.24 10-5M2 12c0 2.76 4.48 5 10 5s10-2.24 10-5',
  LayoutDashboard: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  GitBranch: 'M6 3v12M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 9a9 9 0 0 1-9 9',
  FlaskConical: 'M14 2v6l3 10H7L10 8V2M8.5 2h7',
  Settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
  Lock: 'M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zM7 11V7a5 5 0 0 1 10 0v4',
  Hash: 'M4 9h16M4 15h16M10 3L8 21M16 3l-2 18',
  Activity: 'M22 12h-4l-3 9L9 3l-3 9H2',
  Clock: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2',
  Server: 'M2 3h20v6H2zM2 15h20v6H2zM6 9v6M18 9v6',
  AlertTriangle: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
  CheckCircle: 'M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3',
  XCircle: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM15 9l-6 6M9 9l6 6',
  PlayCircle: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM10 8l6 4-6 4V8z',
  Target: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM22 12h-2M2 12h2M12 2v2M12 22v-2',
  Sparkles: 'M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8L12 3zM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15zM5 15l.9 2.1L8 18l-2.1.9L5 21l-.9-2.1L2 18l2.1-.9L5 15z',
  Inbox: 'M4 4h16v10l-3 4H7l-3-4V4zM4 14h4l2 3h4l2-3h4',
  X: 'M18 6L6 18M6 6l12 12',
}

const CHART_COLORS = ['#FF3621', '#58a6ff', '#3fb950', '#e3b341', '#bc8cff', '#d28c3c']

// ── Render context ─────────────────────────────────────────────────────────
interface RenderCtx {
  dispatch: (event_id: string, data?: Record<string, unknown>) => void
  navigate: (path: string) => void
  pendingEvents: Map<string, number>
  themeMode: 'light' | 'dark'
  setThemeMode: (mode: 'light' | 'dark') => void
}

// ── Icon component ──────────────────────────────────────────────────────────
function resolveIconName(name: string) {
  const cleaned = name
    .replace(/^lucide:/i, '')
    .replace(/^icon:/i, '')
    .trim()

  if (!cleaned) return ''
  if ((LucideIcons as Record<string, unknown>)[cleaned]) return cleaned

  const pascal = cleaned
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('')

  if ((LucideIcons as Record<string, unknown>)[pascal]) return pascal
  return ''
}

type LucideGlyph = React.ComponentType<{
  size?: number
  strokeWidth?: number
  className?: string
}>

function Icon({
  name,
  size = 16,
  strokeWidth = 2,
  className,
}: {
  name: string
  size?: number
  strokeWidth?: number
  className?: string
}) {
  const resolvedName = resolveIconName(name)
  const LucideIcon = resolvedName
    ? (LucideIcons as unknown as Record<string, LucideGlyph>)[resolvedName]
    : undefined
  const legacyPath =
    LUCIDE_ICON_MAP[resolvedName] ||
    LUCIDE_ICON_MAP[name] ||
    LUCIDE_ICON_MAP[name.trim()]

  if (LucideIcon) return React.createElement(LucideIcon, { size, strokeWidth, className })
  if (legacyPath) {
    return (
      <svg
        className={className}
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d={legacyPath} />
      </svg>
    )
  }

  if (!LucideIcon) return <span className={className} style={{ fontSize: size - 2, opacity: 0.6 }}>◆</span>
  return <span className={className} style={{ fontSize: size - 2, opacity: 0.6 }}>*</span>
}

function resolveMotionClass(props: Record<string, any>, base: string[] = []) {
  const classes = [...base]
  if (props.animated) classes.push('bf-animated')
  if (props.elevated) classes.push('bf-elevated')
  if (props.loading) classes.push('bf-is-loading')
  if (props.animation) classes.push(`bf-anim-${props.animation}`)
  return classes.filter(Boolean).join(' ')
}

function resolveMotionStyle(props: Record<string, any>) {
  const style = { ...(props.style as object || {}) } as React.CSSProperties
  if (props.animationDelay !== undefined && props.animationDelay !== null) {
    style.animationDelay = `${props.animationDelay}s`
  }
  return style
}

function pendingEventIds(props: Record<string, any>, keys: string[] = ['click', 'change', 'submit', 'close', 'rowClick', 'nodeClick', 'cardClick']) {
  return keys
    .map((key) => props[key])
    .filter((value): value is string => typeof value === 'string' && value.length > 0)
}

function isPending(props: Record<string, any>, ctx: RenderCtx, keys?: string[]) {
  return pendingEventIds(props, keys).some((eventId) => (ctx.pendingEvents.get(eventId) || 0) > 0)
}

function renderLoadingSkeleton(lines = 3) {
  return (
    <div className="bf-skeleton-stack">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="bf-skeleton-line" />
      ))}
    </div>
  )
}

function PlotComponent({ figure }: { figure: unknown }) {
  const elementRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!elementRef.current) return
    const value = (figure && typeof figure === 'object')
      ? figure as Record<string, unknown>
      : {}
    const data = Array.isArray(value.data) ? value.data : []
    const layout = (value.layout && typeof value.layout === 'object')
      ? value.layout as Record<string, unknown>
      : {}
    const config = (value.config && typeof value.config === 'object')
      ? value.config as Record<string, unknown>
      : { responsive: true }
    const element = elementRef.current
    let active = true
    let purge: (() => void) | undefined
    void import('plotly.js-dist-min').then(({ default: Plotly }) => {
      if (!active) return
      void Plotly.react(element, data, layout, config)
      purge = () => Plotly.purge(element)
    })
    return () => {
      active = false
      purge?.()
    }
  }, [figure])

  return <div ref={elementRef} className="bf-chart-container" />
}

function chartShell(key: string, props: Record<string, any>, content: React.ReactNode) {
  return (
    <div key={key} className="bf-chart-container bf-chart-enter">
      {props.title && <div className="bf-chart-title">{props.title as string}</div>}
      {content}
    </div>
  )
}

function chartState(key: string, props: Record<string, any>) {
  if (props.loading) return <div key={key} className="bf-chart-state">{renderLoadingSkeleton(4)}</div>
  const data = (props.data as unknown[]) || []
  if (!data.length) return <div key={key} className="bf-chart-state">{(props.emptyMessage as string) || 'No chart data available'}</div>
  return null
}

function statusTone(status?: unknown) {
  const normalized = String(status || 'neutral').toLowerCase()
  if (['success', 'healthy', 'ok', 'running', 'passed', 'complete', 'completed'].includes(normalized)) return 'success'
  if (['warning', 'watch', 'delayed', 'queued', 'degraded'].includes(normalized)) return 'warning'
  if (['error', 'failed', 'critical', 'blocked', 'at risk', 'atrisk'].includes(normalized)) return 'error'
  if (['info', 'active', 'processing'].includes(normalized)) return 'info'
  return 'neutral'
}

// ── Main recursive renderer ────────────────────────────────────────────────
export function Renderer({
  node,
  dispatch,
  navigate,
  pendingEvents,
  themeMode,
  setThemeMode,
}: {
  node: VNodeData
  dispatch: RenderCtx['dispatch']
  navigate: RenderCtx['navigate']
  pendingEvents: Map<string, number>
  themeMode: 'light' | 'dark'
  setThemeMode: (mode: 'light' | 'dark') => void
}) {
  const ctx: RenderCtx = { dispatch, navigate, pendingEvents, themeMode, setThemeMode }
  return <>{renderNode(node, ctx, '0')}</>
}

function renderChildren(children: VNodeData[], ctx: RenderCtx, prefix: string) {
  return children.map((child, i) => renderNode(child, ctx, `${prefix}-${i}`))
}

function renderNode(node: VNodeData, ctx: RenderCtx, key: string): React.ReactNode {
  if (!node) return null
  const { type, props, children } = node
  const p = props as Record<string, any>

  const ev = (eventName: string, arg?: unknown) => {
    const eventId = p[eventName] as string | undefined
    if (eventId) ctx.dispatch(eventId, arg === undefined ? {} : { value: arg })
  }

  switch (type) {

    // ── Text ───────────────────────────────────────────────────────────────
    case 'Text': {
      const variant = (p.variant as string) || 'body'
      const cls = ['bf-text-' + variant, p.muted ? 'bf-text-muted' : '', p.bold ? 'bf-text-bold' : '', p.italic ? 'bf-text-italic' : '', p.className as string || ''].filter(Boolean).join(' ')
      const Tag = ({ h1: 'h1', h2: 'h2', h3: 'h3', h4: 'h4', code: 'code', label: 'label', caption: 'small' } as Record<string, string>)[variant] || 'p'
      const style = { ...(p.style as object || {}) } as React.CSSProperties
      if (p.color) style.color = p.color as string
      return React.createElement(Tag, { key, className: cls, style: Object.keys(style).length ? style : undefined }, p.value as string)
    }

    case 'Code':
      return <pre key={key} className="bf-code-block"><code>{p.value as string}</code></pre>

    // ── Layout ─────────────────────────────────────────────────────────────
    case 'Column': {
      const pad = ((p.padding as number) || 0) * 4
      const gap = ((p.gap as number) || 2) * 4
      const alignMap: Record<string, string> = { start: 'flex-start', end: 'flex-end', center: 'center', stretch: 'stretch' }
      return (
        <div key={key} className="bf-column" style={{ display: 'flex', flexDirection: 'column', gap, padding: pad, alignItems: alignMap[p.align as string] || 'stretch', width: '100%', ...(p.style as object || {}) }}>
          {renderChildren(children, ctx, key)}
        </div>
      )
    }

    case 'Row': {
      const gap = ((p.gap as number) || 2) * 4
      const alignMap: Record<string, string> = { start: 'flex-start', end: 'flex-end', center: 'center', stretch: 'stretch' }
      const justifyMap: Record<string, string> = { start: 'flex-start', end: 'flex-end', center: 'center', between: 'space-between', around: 'space-around' }
      return (
        <div key={key} className="bf-row" style={{ display: 'flex', flexDirection: 'row', gap, flexWrap: p.wrap !== false ? 'wrap' : 'nowrap', alignItems: alignMap[p.align as string] || 'center', justifyContent: justifyMap[p.justify as string] || 'flex-start', width: '100%', ...(p.style as object || {}) }}>
          {renderChildren(children, ctx, key)}
        </div>
      )
    }

    case 'Card': {
      const cls = resolveMotionClass(p, ['bf-card', p.bordered ? 'bordered' : '', p.hover ? 'hoverable' : ''])
      const pad = ((p.padding as number) || 5) * 4
      return (
        <div key={key} className={cls} style={{ padding: pad, ...resolveMotionStyle(p) }}>
          {(p.title || p.subtitle) ? (
            <div className="bf-card-header">
              {p.title ? <div className="bf-card-title">{p.title as string}</div> : null}
              {p.subtitle ? <div className="bf-card-subtitle">{p.subtitle as string}</div> : null}
            </div>
          ) : null}
          {renderChildren(children, ctx, key)}
        </div>
      )
    }

    case 'Grid': {
      const cols = (p.cols as number) || 2
      const gap = ((p.gap as number) || 4) * 4
      return (
        <div key={key} className="bf-grid" style={{ '--cols': cols, gap } as React.CSSProperties}>
          {renderChildren(children, ctx, key)}
        </div>
      )
    }

    case 'Divider':
      return p.label
        ? <div key={key} className="bf-divider-labeled"><span>{p.label as string}</span></div>
        : <hr key={key} className="bf-divider" />

    case 'Spacer':
      return <div key={key} style={{ height: ((p.size as number) || 4) * 4 }} />

    // ── Controls ───────────────────────────────────────────────────────────
    case 'Button':
      {
      const autoLoading = isPending(p, ctx, ['click'])
      return (
        <button
          key={key}
          className={resolveMotionClass({ ...p, loading: Boolean(p.loading) || autoLoading }, ['bf-btn', `bf-btn-${(p.variant as string) || 'primary'}`])}
          disabled={(p.disabled as boolean) || (p.loading as boolean) || autoLoading || false}
          type={(p.htmlType as 'button' | 'submit' | 'reset') || 'button'}
          style={resolveMotionStyle(p)}
          onClick={() => ev('click')}
        >
          {(p.loading || autoLoading) && <span className="bf-spinner bf-spinner-sm" />}
          {p.icon && <Icon name={p.icon as string} size={14} />}
          {p.label as string}
        </button>
      )
      }

    case 'Input':
      return <InputComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    case 'DateRangePicker':
      return <DateRangePickerComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    case 'MultiSelect':
      return <MultiSelectComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    case 'Select':
      return <SelectComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    case 'Checkbox':
      return <CheckboxComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    case 'Toggle': {
      return (
        <ToggleComponent key={key} props={p} dispatch={(v) => ev('change', v)} pending={isPending(p, ctx, ['change'])} />
      )
    }

    case 'Slider':
      return <SliderComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['change']) }} dispatch={(value) => ev('change', value)} />

    // ── Data display ───────────────────────────────────────────────────────
    case 'Breadcrumbs':
      return (
        <nav key={key} className="bf-breadcrumbs" aria-label="Breadcrumb">
          {((p.items as Array<Record<string, any>>) || []).map((item, index, items) => {
            const isLast = index === items.length - 1
            return (
              <React.Fragment key={`${key}-crumb-${index}`}>
                {isLast || !item.path ? (
                  <span className="bf-breadcrumb-current">{String(item.label ?? '')}</span>
                ) : (
                  <button type="button" className="bf-breadcrumb-link" onClick={() => ctx.navigate(String(item.path))}>
                    {String(item.label ?? '')}
                  </button>
                )}
                {!isLast ? <span className="bf-breadcrumb-sep">/</span> : null}
              </React.Fragment>
            )
          })}
        </nav>
      )

    case 'EmptyState':
      return (
        <div key={key} className={resolveMotionClass(p, ['bf-empty-state'])} style={resolveMotionStyle(p)}>
          <div className="bf-empty-state-icon">
            <Icon name={(p.icon as string) || 'Inbox'} size={18} />
          </div>
          <div className="bf-empty-state-title">{p.title as string}</div>
          <div className="bf-empty-state-message">{p.message as string}</div>
          {(p.actions as VNodeData[] | undefined)?.length ? (
            <div className="bf-empty-state-actions">
              {renderChildren((p.actions as VNodeData[]) || [], ctx, `${key}-actions`)}
            </div>
          ) : null}
        </div>
      )

    case 'Table':
      return <TableComponent key={key} props={p} dispatch={ctx.dispatch} />

    case 'Badge':
      return <span key={key} className={`bf-badge bf-badge-${(p.color as string) || 'blue'} ${p.className || ''}`.trim()} style={p.style as React.CSSProperties | undefined}>{p.label as string}</span>

    case 'Alert':
      return <AlertComponent key={key} props={p} />

    case 'Spinner':
      return <div key={key} className={`bf-spinner bf-spinner-${(p.size as string) || 'md'}`} />

    case 'Progress': {
      const pct = Math.min(100, (((p.value as number) / (p.max as number || 100)) * 100))
      return (
        <div key={key} className={resolveMotionClass(p, ['bf-progress-wrapper'])} style={resolveMotionStyle(p)}>
          {p.label && <div className="bf-progress-label"><span>{p.label as string}</span><span>{Math.round(pct)}%</span></div>}
          <div className="bf-progress-track">
            <div className={`bf-progress-fill ${p.animated ? 'animated' : ''}`} style={{ width: `${pct}%`, background: `var(--db-${p.color || 'primary'})` }} />
          </div>
        </div>
      )
    }

    case 'Stat': {
      const deltaType = (p.deltaType as string) || 'neutral'
      return (
        <div key={key} className={resolveMotionClass(p, ['bf-stat'])} style={resolveMotionStyle(p)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {p.icon && <Icon name={p.icon as string} size={16} />}
            <div className="bf-stat-label">{p.label as string}</div>
          </div>
          <AnimatedValue value={p.value as string} animated={Boolean(p.animated)} />
          {p.delta && <div className={`bf-stat-delta ${deltaType}`}>{deltaType === 'increase' ? '▲' : deltaType === 'decrease' ? '▼' : '—'} {p.delta as string}</div>}
        </div>
      )
    }

    // ── Navigation ──────────────────────────────────────────────────────────
    case 'Sidebar':
      return <SidebarComponent key={key} props={p} children={children} ctx={ctx} />

    case 'TopNav':
      return <TopNavComponent key={key} props={p} children={children} ctx={ctx} />

    // NavItem is rendered as part of Sidebar above; standalone fallback:
    case 'NavItem':
      return (
        <button key={key} className="bf-nav-item" onClick={() => ctx.navigate(p.path as string)}>
          {p.icon && <Icon name={p.icon as string} size={16} />}
          {p.label as string}
        </button>
      )

    // ── Tabs ───────────────────────────────────────────────────────────────
    case 'Tabs':
      return <TabsComponent key={key} props={p} children={children} ctx={ctx} nodeKey={key} dispatch={ctx.dispatch} />

    case 'TabItem':
      return null // Rendered inside Tabs

    // ── Modal ──────────────────────────────────────────────────────────────
    case 'Accordion':
      return <AccordionComponent key={key} props={p} children={children} ctx={ctx} nodeKey={key} />

    case 'AccordionItem':
      return null

    case 'Modal':
      if (!p.visible) return null
      return (
        <div key={key} className="bf-modal-overlay" onClick={() => ev('close')}>
          <div role="dialog" aria-modal="true" aria-label={String(p.title || 'Dialog')} className={resolveMotionClass(p, [`bf-modal`, `bf-modal-${(p.size as string) || 'md'}`])} style={resolveMotionStyle(p)} onClick={e => e.stopPropagation()}>
            <div className="bf-modal-header">
              <span className="bf-modal-title">{p.title as string}</span>
              <button type="button" className="bf-modal-close" onClick={() => ev('close')} aria-label="Close dialog"><Icon name="X" size={16} /></button>
            </div>
            <div className="bf-modal-body">{renderChildren(children, ctx, key)}</div>
          </div>
        </div>
      )

    // ── Form ───────────────────────────────────────────────────────────────
    case 'Drawer':
      if (!p.visible) return null
      return (
        <div key={key} className="bf-drawer-overlay" onClick={() => ev('close')}>
          <div role="dialog" aria-modal="true" aria-label={String(p.title || 'Drawer')} className={resolveMotionClass(p, [`bf-drawer`, `bf-drawer-${(p.side as string) || 'right'}`])} style={{ width: (p.width as string) || '420px', ...resolveMotionStyle(p) }} onClick={e => e.stopPropagation()}>
            <div className="bf-drawer-header">
              <span className="bf-drawer-title">{p.title as string}</span>
              <button type="button" className="bf-modal-close" onClick={() => ev('close')} aria-label="Close drawer"><Icon name="X" size={16} /></button>
            </div>
            <div className="bf-drawer-body">{renderChildren(children, ctx, key)}</div>
          </div>
        </div>
      )

    case 'Popup':
      if (!p.visible) return null
      return (
        <div key={key} className={`bf-popup-shell bf-popup-${(p.placement as string) || 'center'}`}>
          {Boolean(p.backdrop) ? <button type="button" className="bf-popup-backdrop" onClick={() => ev('close')} aria-label="Close popup" /> : null}
          <div role="dialog" aria-modal={Boolean(p.backdrop)} aria-label={String(p.title || 'Popup')} className={resolveMotionClass(p, [`bf-popup`, `bf-popup-${(p.size as string) || 'sm'}`])} style={resolveMotionStyle(p)} onClick={e => e.stopPropagation()}>
            <div className="bf-popup-header">
              <span className="bf-popup-title">{p.title as string}</span>
              <button type="button" className="bf-modal-close" onClick={() => ev('close')}><Icon name="X" size={16} /></button>
            </div>
            <div className="bf-popup-body">{renderChildren(children, ctx, key)}</div>
          </div>
        </div>
      )

    case 'Form':
      return <FormComponent key={key} props={p} children={children} ctx={ctx} nodeKey={key} />

    // ── Charts ─────────────────────────────────────────────────────────────
    case 'Plot':
      return <PlotComponent key={key} figure={p.figure} />

    case 'AreaChart': {
      const yKeys = (p.yKeys as string[]) || []
      const data = (p.data as object[]) || []
      if (p.loading) return <div key={key} className="bf-chart-state">{renderLoadingSkeleton(4)}</div>
      if (!data.length) return <div key={key} className="bf-chart-state">{(p.emptyMessage as string) || 'No chart data available'}</div>
      return (
        <div key={key} className="bf-chart-container">
          {p.title && <div className="bf-chart-title">{p.title as string}</div>}
          <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
            <AreaChart data={data} onClick={(state) => p.click && ev('click', state?.activePayload?.[0]?.payload ?? {})}>
              <defs>
                {yKeys.map((yk, i) => (
                  <linearGradient key={yk} id={`agrad-${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={(p.colors as string[])?.[i] || CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={(p.colors as string[])?.[i] || CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={p.xKey as string} />
              <YAxis />
              <Tooltip />
              {yKeys.map((yk, i) => (
                <Area key={yk} type="monotone" dataKey={yk} stroke={(p.colors as string[])?.[i] || CHART_COLORS[i % CHART_COLORS.length]} fill={`url(#agrad-${i})`} strokeWidth={2} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )
    }

    case 'LineChart': {
      const yKeys = (p.yKeys as string[]) || []
      const data = (p.data as object[]) || []
      if (p.loading) return <div key={key} className="bf-chart-state">{renderLoadingSkeleton(4)}</div>
      if (!data.length) return <div key={key} className="bf-chart-state">{(p.emptyMessage as string) || 'No chart data available'}</div>
      return (
        <div key={key} className="bf-chart-container">
          {p.title && <div className="bf-chart-title">{p.title as string}</div>}
          <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
            <LineChart data={data} onClick={(state) => p.click && ev('click', state?.activePayload?.[0]?.payload ?? {})}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={p.xKey as string} />
              <YAxis />
              <Tooltip />
              <Legend />
              {yKeys.map((yk, i) => (
                <Line key={yk} type="monotone" dataKey={yk} stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )
    }

    case 'BarChart': {
      const yKeys = (p.yKeys as string[]) || []
      const data = (p.data as object[]) || []
      if (p.loading) return <div key={key} className="bf-chart-state">{renderLoadingSkeleton(4)}</div>
      if (!data.length) return <div key={key} className="bf-chart-state">{(p.emptyMessage as string) || 'No chart data available'}</div>
      return (
        <div key={key} className="bf-chart-container">
          {p.title && <div className="bf-chart-title">{p.title as string}</div>}
          <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
            <BarChart data={data} layout={p.horizontal ? 'vertical' : 'horizontal'} onClick={(state) => p.click && ev('click', state?.activePayload?.[0]?.payload ?? {})}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={p.horizontal ? undefined : p.xKey as string} type={p.horizontal ? 'number' : 'category'} />
              <YAxis dataKey={p.horizontal ? p.xKey as string : undefined} type={p.horizontal ? 'category' : 'number'} />
              <Tooltip />
              {yKeys.map((yk, i) => (
                <Bar key={yk} dataKey={yk} fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )
    }

    case 'DonutChart': {
      const data = (p.data as Array<{ [k: string]: unknown }>) || []
      const vk = (p.valueKey as string) || 'value'
      const lk = (p.labelKey as string) || 'label'
      if (p.loading) return <div key={key} className="bf-chart-state">{renderLoadingSkeleton(4)}</div>
      if (!data.length) return <div key={key} className="bf-chart-state">{(p.emptyMessage as string) || 'No chart data available'}</div>
      return (
        <div key={key} className="bf-chart-container">
          {p.title && <div className="bf-chart-title">{p.title as string}</div>}
          <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius="55%" outerRadius="75%" dataKey={vk} nameKey={lk} paddingAngle={2} onClick={(payload) => p.click && ev('click', payload?.payload ?? {})}>
                {data.map((_, i) => <Cell key={i} fill={((p.colors as string[]) || [])[i] || CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(value, name) => [value, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )
    }

    case 'ScatterChart': {
      const state = chartState(key, p)
      if (state) return state
      return chartShell(key, p,
        <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
          <ReScatterChart data={(p.data as object[]) || []} onClick={(state) => p.click && ev('click', state?.activePayload?.[0]?.payload ?? {})}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={p.xKey as string} type="number" name={p.xKey as string} />
            <YAxis dataKey={p.yKey as string} type="number" name={p.yKey as string} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter dataKey={p.yKey as string} fill={(p.color as string) || CHART_COLORS[0]} />
          </ReScatterChart>
        </ResponsiveContainer>
      )
    }

    case 'ComposedChart': {
      const state = chartState(key, p)
      if (state) return state
      const colors = (p.colors as string[]) || CHART_COLORS
      return chartShell(key, p,
        <ResponsiveContainer width="100%" height={(p.height as number) || 320}>
          <ReComposedChart data={(p.data as object[]) || []} onClick={(state) => p.click && ev('click', state?.activePayload?.[0]?.payload ?? {})}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={p.xKey as string} />
            <YAxis />
            <Tooltip />
            <Legend />
            {((p.areaKeys as string[]) || []).map((yk, i) => (
              <Area key={`area-${yk}`} type="monotone" dataKey={yk} fill={colors[i % colors.length]} stroke={colors[i % colors.length]} fillOpacity={0.18} />
            ))}
            {((p.barKeys as string[]) || []).map((yk, i) => (
              <Bar key={`bar-${yk}`} dataKey={yk} fill={colors[(i + 2) % colors.length]} radius={[3, 3, 0, 0]} />
            ))}
            {((p.lineKeys as string[]) || []).map((yk, i) => (
              <Line key={`line-${yk}`} type="monotone" dataKey={yk} stroke={colors[(i + 4) % colors.length]} strokeWidth={2} dot={false} />
            ))}
          </ReComposedChart>
        </ResponsiveContainer>
      )
    }

    case 'GaugeChart':
      return <GaugeChartComponent key={key} props={p} />

    case 'RadarChart': {
      const state = chartState(key, p)
      if (state) return state
      const colors = (p.colors as string[]) || CHART_COLORS
      return chartShell(key, p,
        <ResponsiveContainer width="100%" height={(p.height as number) || 320}>
          <ReRadarChart data={(p.data as object[]) || []}>
            <PolarGrid />
            <PolarAngleAxis dataKey={p.angleKey as string} />
            <PolarRadiusAxis />
            <Tooltip />
            <Legend />
            {((p.valueKeys as string[]) || []).map((yk, i) => (
              <Radar key={yk} name={yk} dataKey={yk} stroke={colors[i % colors.length]} fill={colors[i % colors.length]} fillOpacity={0.18} />
            ))}
          </ReRadarChart>
        </ResponsiveContainer>
      )
    }

    case 'Heatmap':
      return <HeatmapComponent key={key} props={p} dispatch={(value) => ev('click', value)} />

    case 'FunnelChart': {
      const state = chartState(key, p)
      if (state) return state
      const data = (p.data as Array<Record<string, unknown>>) || []
      return chartShell(key, p,
        <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
          <ReFunnelChart>
            <Tooltip />
            <Funnel dataKey={(p.valueKey as string) || 'value'} nameKey={(p.labelKey as string) || 'label'} data={data} isAnimationActive onClick={(payload) => p.click && ev('click', payload?.payload ?? {})}>
              {data.map((_, i) => <Cell key={i} fill={((p.colors as string[]) || [])[i] || CHART_COLORS[i % CHART_COLORS.length]} />)}
            </Funnel>
          </ReFunnelChart>
        </ResponsiveContainer>
      )
    }

    case 'TreeMap': {
      const state = chartState(key, p)
      if (state) return state
      return chartShell(key, p,
        <ResponsiveContainer width="100%" height={(p.height as number) || 300}>
          <Treemap
            data={(p.data as object[]) || []}
            dataKey={(p.valueKey as string) || 'value'}
            nameKey={(p.nameKey as string) || 'name'}
            stroke="var(--db-surface)"
            fill={((p.colors as string[]) || [])[0] || CHART_COLORS[0]}
            onClick={(payload) => p.click && ev('click', payload?.payload ?? payload ?? {})}
          />
        </ResponsiveContainer>
      )
    }

    case 'PipelineGraph':
      return <PipelineGraphComponent key={key} props={p} dispatch={(value) => ev('nodeClick', value)} />

    case 'Hero':
      return (
        <section key={key} className={resolveMotionClass(p, ['bf-hero'])} style={resolveMotionStyle(p)}>
          <div className="bf-hero-content">
            {p.eyebrow ? <div className="bf-hero-eyebrow">{p.eyebrow as string}</div> : null}
            {p.image ? (
              <div className="bf-hero-brand">
                <img className="bf-hero-brand-image" src={p.image as string} alt={(p.imageAlt as string) || (p.title as string)} />
                {p.tagline ? <span className="bf-hero-brand-tagline">{p.tagline as string}</span> : null}
              </div>
            ) : p.tagline ? <div className="bf-hero-brand-tagline">{p.tagline as string}</div> : null}
            <h1 className="bf-hero-title">{p.title as string}</h1>
            {p.subtitle ? <p className="bf-hero-subtitle">{p.subtitle as string}</p> : null}
            {(p.badges as VNodeData[] | undefined)?.length ? <div className="bf-hero-badges">{renderChildren((p.badges as VNodeData[]) || [], ctx, `${key}-badges`)}</div> : null}
            {(p.actions as VNodeData[] | undefined)?.length ? <div className="bf-hero-actions">{renderChildren((p.actions as VNodeData[]) || [], ctx, `${key}-actions`)}</div> : null}
          </div>
          {children.length ? <div className="bf-hero-visual">{renderChildren(children, ctx, `${key}-visual`)}</div> : null}
        </section>
      )

    case 'SectionHeader':
      return (
        <div key={key} className={resolveMotionClass(p, ['bf-section-header'])} style={resolveMotionStyle(p)}>
          <div>
            {p.eyebrow ? <div className="bf-section-eyebrow">{p.eyebrow as string}</div> : null}
            <div className="bf-section-title">{p.title as string}</div>
            {p.subtitle ? <div className="bf-section-subtitle">{p.subtitle as string}</div> : null}
          </div>
          {(p.actions as VNodeData[] | undefined)?.length ? <div className="bf-section-actions">{renderChildren((p.actions as VNodeData[]) || [], ctx, `${key}-actions`)}</div> : null}
        </div>
      )

    case 'StatusStrip':
      return <StatusStripComponent key={key} props={p} />

    case 'Stepper':
      return <StepperComponent key={key} props={p} />

    case 'KanbanBoard':
      return <KanbanBoardComponent key={key} props={p} dispatch={(value) => ev('cardClick', value)} />

    case 'ChatMessage':
      return <ChatMessageComponent key={key} props={p} />

    case 'ChatInput':
      return <ChatInputComponent key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['submit', 'change']) }} dispatchChange={(value) => ev('change', value)} dispatchSubmit={(value) => ev('submit', value)} />

    case 'Toast':
      return <ToastComponent key={key} props={p} dispatchClose={() => ev('close')} />

    case 'Image':
      return <ImageComponent key={key} props={p} />

    case 'Video':
      return <VideoComponent key={key} props={p} />

    case 'Embed':
      return <EmbedComponent key={key} props={p} />

    case 'ThemeToggle':
      return <ThemeToggleComponent key={key} props={p} ctx={ctx} />

    case 'Timeline':
      return (
        <div key={key} className={resolveMotionClass(p, ['bf-timeline'])} style={resolveMotionStyle(p)}>
          {p.title ? <div className="bf-card-title" style={{ marginBottom: 12 }}>{p.title as string}</div> : null}
          {((p.items as Array<Record<string, any>>) || []).map((item, index) => (
            <div key={`${key}-timeline-${index}`} className="bf-timeline-item">
              <div className="bf-timeline-dot" />
              <div className="bf-timeline-content">
                <div className="bf-timeline-row">
                  <div className="bf-timeline-title">{String(item.title ?? '')}</div>
                  {item.time ? <div className="bf-timeline-time">{String(item.time)}</div> : null}
                </div>
                {item.subtitle ? <div className="bf-timeline-subtitle">{String(item.subtitle)}</div> : null}
                {item.description ? <div className="bf-timeline-description">{String(item.description)}</div> : null}
              </div>
            </div>
          ))}
        </div>
      )

    case 'SparklineStat':
      return <SparklineStatComponent key={key} props={p} />

    case 'CatalogBrowser':
      return <CatalogBrowserView key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['select']) }} onSelect={(value) => ev('select', value)} />

    case 'WarehouseSelector':
      return <WarehouseSelectorView key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, ['select']) }} onSelect={(value) => ev('select', value)} />

    case 'JobTrigger': {
      const eventName = p.trigger ? 'trigger' : 'complete'
      return <JobTriggerView key={key} props={{ ...p, loading: Boolean(p.loading) || isPending(p, ctx, [eventName]) }} onTrigger={(value) => ev(eventName, value)} />
    }

    default:
      return (
        <div key={key} className={`bf-node-${type.toLowerCase()}`}>
          {renderChildren(children, ctx, key)}
        </div>
      )
  }
}

// ── Sub-components (need their own state) ─────────────────────────────────

function ToggleComponent({ props: p, dispatch, pending }: { props: Record<string, any>; dispatch: (v: boolean) => void; pending: boolean }) {
  const incomingChecked = Boolean(p.checked)
  const [checked, setChecked] = useState(incomingChecked)

  useEffect(() => {
    setChecked(incomingChecked)
  }, [incomingChecked])

  return (
    <label
      className={resolveMotionClass(p, [`bf-toggle-wrapper`, pending ? 'is-loading' : ''])}
      style={resolveMotionStyle(p)}
      onClick={() => {
        if (!p.disabled && !pending) {
          const next = !checked
          setChecked(next)
          dispatch(next)
        }
      }}
    >
      <div className={`bf-toggle-switch ${checked ? 'checked' : ''}`} />
      {p.label as string}
      {pending ? <span className="bf-spinner bf-spinner-sm" /> : null}
    </label>
  )
}

function CheckboxComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: boolean) => void }) {
  const incomingChecked = Boolean(p.checked)
  const [checked, setChecked] = useState(incomingChecked)

  useEffect(() => {
    setChecked(incomingChecked)
  }, [incomingChecked])

  return (
    <label className={resolveMotionClass(p, ['bf-checkbox-wrapper', p.loading ? 'is-loading' : ''])} style={resolveMotionStyle(p)}>
      <input
        type="checkbox"
        name={p.name as string}
        checked={checked}
        disabled={Boolean(p.disabled) || Boolean(p.loading)}
        onChange={(event) => {
          const next = event.target.checked
          setChecked(next)
          dispatch(next)
        }}
      />
      {p.label as string}
      {p.loading ? <span className="bf-spinner bf-spinner-sm" /> : null}
    </label>
  )
}

function SelectComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: string) => void }) {
  const generatedId = useId()
  const selectId = String(p.id || p.name || `bf-select-${generatedId}`)
  const incomingValue = String((p.value as string) || '')
  const [value, setValue] = useState(incomingValue)

  useEffect(() => {
    setValue(incomingValue)
  }, [incomingValue])

  return (
    <div className={resolveMotionClass(p, ['bf-form-field'])} style={resolveMotionStyle(p)}>
      {p.label && <label className="bf-label" htmlFor={selectId}>{p.label as string}</label>}
      {p.loading ? <div className="bf-field-loading"><div className="bf-spinner bf-spinner-sm" /></div> : null}
      <select
        id={selectId}
        name={p.name as string}
        className="bf-select"
        value={value}
        disabled={Boolean(p.disabled) || Boolean(p.loading)}
        onChange={(event) => {
          const next = event.target.value
          setValue(next)
          dispatch(next)
        }}
      >
        {p.placeholder ? <option value="">{p.placeholder as string}</option> : null}
        {((p.options as Array<{ label: string; value: string }>) || []).map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

function SliderComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: number) => void }) {
  const generatedId = useId()
  const sliderId = String(p.id || p.name || `bf-slider-${generatedId}`)
  const incomingValue = Number(p.value ?? 0)
  const [value, setValue] = useState(incomingValue)

  useEffect(() => {
    setValue(incomingValue)
  }, [incomingValue])

  return (
    <div className={resolveMotionClass(p, ['bf-slider-wrapper', p.loading ? 'bf-is-loading' : ''])} style={resolveMotionStyle(p)}>
      {p.label && <label className="bf-label" htmlFor={sliderId}>{p.label as string}</label>}
      <input
        id={sliderId}
        type="range"
        className="bf-slider"
        name={p.name as string}
        min={p.min as number}
        max={p.max as number}
        step={p.step as number}
        value={value}
        disabled={Boolean(p.disabled) || Boolean(p.loading)}
        onChange={(event) => {
          const next = parseFloat(event.target.value)
          setValue(next)
          dispatch(next)
        }}
      />
      {p.loading ? <div className="bf-field-loading"><div className="bf-spinner bf-spinner-sm" /></div> : null}
    </div>
  )
}

function AlertComponent({ props: p }: { props: Record<string, any> }) {
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    setDismissed(false)
  }, [p.message, p.title, p.alertType])

  if (dismissed) return null

  return (
    <div className={`bf-alert bf-alert-${(p.alertType as string) || 'info'}`}>
      <div className="bf-alert-body">
        {p.title ? <div className="bf-alert-title">{p.title as string}</div> : null}
        <div>{p.message as string}</div>
      </div>
      {Boolean(p.dismissible) ? (
        <button type="button" className="bf-alert-close" onClick={() => setDismissed(true)} aria-label="Dismiss alert">
          <Icon name="X" size={14} />
        </button>
      ) : null}
    </div>
  )
}

function ImageComponent({ props: p }: { props: Record<string, any> }) {
  const variant = (p.variant as string) || 'content'
  const image = (
    <img
      className={`bf-image ${variant === 'inline' ? 'inline' : ''} ${variant === 'avatar' ? 'avatar' : ''}`}
      src={p.src as string}
      alt={(p.alt as string) || ''}
      loading={(p.loadingMode as 'lazy' | 'eager') || 'lazy'}
      style={{
        width: (p.width as string) || (variant === 'avatar' ? '48px' : '100%'),
        height: (p.height as string) || (variant === 'avatar' ? ((p.width as string) || '48px') : 'auto'),
        objectFit: (p.fit as React.CSSProperties['objectFit']) || 'cover',
        borderRadius: variant === 'avatar' ? '50%' : ((p.radius as string) || 'var(--radius-lg)'),
      }}
    />
  )

  if (variant === 'inline' && !p.caption) {
    return (
      <span className={resolveMotionClass(p, ['bf-inline-image'])} style={resolveMotionStyle(p)}>
        {image}
      </span>
    )
  }

  return (
    <figure className={resolveMotionClass(p, ['bf-image-shell', p.caption ? 'has-caption' : ''])} style={resolveMotionStyle(p)}>
      {image}
      {p.caption ? <figcaption className="bf-image-caption">{p.caption as string}</figcaption> : null}
    </figure>
  )
}

function VideoComponent({ props: p }: { props: Record<string, any> }) {
  return (
    <figure className={resolveMotionClass(p, ['bf-image-shell', 'bf-video-shell', p.caption ? 'has-caption' : ''])} style={resolveMotionStyle(p)}>
      <video
        className="bf-video"
        src={p.src as string}
        poster={p.poster as string | undefined}
        controls={p.controls !== false}
        autoPlay={Boolean(p.autoplay)}
        loop={Boolean(p.loop)}
        muted={Boolean(p.muted)}
        playsInline
        style={{
          width: (p.width as string) || '100%',
          height: (p.height as string) || 'auto',
          borderRadius: (p.radius as string) || 'var(--radius-lg)',
        }}
      />
      {p.caption ? <figcaption className="bf-image-caption">{p.caption as string}</figcaption> : null}
    </figure>
  )
}

function EmbedComponent({ props: p }: { props: Record<string, any> }) {
  return (
    <div className={resolveMotionClass(p, ['bf-embed-shell'])} style={resolveMotionStyle(p)}>
      <iframe
        className="bf-embed-frame"
        src={p.src as string}
        title={(p.title as string) || 'Embedded content'}
        loading={(p.loadingMode as 'lazy' | 'eager') || 'lazy'}
        sandbox={typeof p.sandbox === 'string' ? (p.sandbox as string) : undefined}
        allowFullScreen={Boolean(p.allowFullscreen)}
        style={{
          height: (p.height as string) || '420px',
          borderRadius: (p.radius as string) || 'var(--radius-lg)',
        }}
      />
    </div>
  )
}

function ThemeToggleComponent({ props: p, ctx }: { props: Record<string, any>; ctx: RenderCtx }) {
  const isDark = ctx.themeMode === 'dark'
  return (
    <button
      type="button"
      className="bf-theme-toggle"
      onClick={() => ctx.setThemeMode(isDark ? 'light' : 'dark')}
      aria-label={String(p.label || 'Toggle theme')}
    >
      <span className="bf-theme-toggle-track">
        <span className={`bf-theme-toggle-thumb ${isDark ? 'dark' : 'light'}`} />
      </span>
      <span className="bf-theme-toggle-copy">
        <strong>{String(p.label || 'Theme')}</strong>
        <span>{isDark ? String(p.darkLabel || 'Dark') : String(p.lightLabel || 'Light')}</span>
      </span>
    </button>
  )
}

function ToastComponent({ props: p, dispatchClose }: { props: Record<string, any>; dispatchClose: () => void }) {
  const [dismissed, setDismissed] = useState(false)
  const close = () => {
    setDismissed(true)
    if (p.close) dispatchClose()
  }

  useEffect(() => {
    setDismissed(false)
  }, [p.visible, p.message, p.title, p.alertType])

  useEffect(() => {
    if (!p.autoHideMs || dismissed || p.visible === false) return
    const timer = window.setTimeout(() => close(), Number(p.autoHideMs))
    return () => window.clearTimeout(timer)
  }, [dismissed, p.autoHideMs, p.visible, p.message, p.title])

  if (p.visible === false || dismissed) return null

  return (
    <div className={resolveMotionClass(p, [`bf-toast`, `bf-toast-${(p.alertType as string) || 'info'}`])} style={resolveMotionStyle(p)}>
      {p.icon ? <Icon name={p.icon as string} size={16} /> : null}
      <div className="bf-toast-content">
        {p.title ? <div className="bf-toast-title">{p.title as string}</div> : null}
        <div className="bf-toast-message">{p.message as string}</div>
      </div>
      {p.dismissible !== false ? (
        <button type="button" className="bf-toast-close" onClick={close} aria-label="Dismiss notification">
          <Icon name="X" size={14} />
        </button>
      ) : null}
    </div>
  )
}

function AnimatedValue({ value, animated }: { value: string; animated: boolean }) {
  const parseNumeric = (raw: string) => {
    const match = raw.match(/-?\d+(?:\.\d+)?/)
    if (!match) return null
    return {
      number: parseFloat(match[0]),
      prefix: raw.slice(0, match.index ?? 0),
      suffix: raw.slice((match.index ?? 0) + match[0].length),
      decimals: match[0].includes('.') ? match[0].split('.')[1].length : 0,
    }
  }

  const parsed = parseNumeric(value)
  const [display, setDisplay] = useState(() => {
    if (!animated || !parsed) return value
    return `${parsed.prefix}${(0).toFixed(parsed.decimals)}${parsed.suffix}`
  })

  useEffect(() => {
    if (!animated || !parsed) {
      setDisplay(value)
      return
    }

    const duration = 700
    const start = performance.now()

    let frame = 0
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = parsed.number * eased
      setDisplay(`${parsed.prefix}${current.toFixed(parsed.decimals)}${parsed.suffix}`)
      if (progress < 1) frame = requestAnimationFrame(tick)
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [animated, parsed?.decimals, parsed?.number, parsed?.prefix, parsed?.suffix, value])

  return <div className="bf-stat-value">{display}</div>
}

function useDebouncedDispatcher<T>(dispatch: (value: T) => void, delayMs: number) {
  const latestDispatch = useRef(dispatch)
  const timerRef = useRef<number | null>(null)
  const queuedValueRef = useRef<T | null>(null)

  useEffect(() => {
    latestDispatch.current = dispatch
  }, [dispatch])

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
      }
    }
  }, [])

  const flush = useCallback((explicitValue?: T) => {
    const nextValue = explicitValue ?? queuedValueRef.current
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
    if (nextValue === null || nextValue === undefined) return
    queuedValueRef.current = null
    latestDispatch.current(nextValue)
  }, [])

  const schedule = useCallback((value: T) => {
    queuedValueRef.current = value
    if (delayMs <= 0) {
      flush(value)
      return
    }
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
    }
    timerRef.current = window.setTimeout(() => {
      const queued = queuedValueRef.current
      queuedValueRef.current = null
      timerRef.current = null
      if (queued !== null && queued !== undefined) {
        latestDispatch.current(queued)
      }
    }, delayMs)
  }, [delayMs, flush])

  return { flush, schedule }
}

function InputComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: string) => void }) {
  const generatedId = useId()
  const inputId = String(p.id || p.name || `bf-input-${generatedId}`)
  const errorId = `${inputId}-error`
  const incomingValue = String((p.value as string) || '')
  const [value, setValue] = useState(incomingValue)
  const localDirtyRef = useRef(false)
  const lastDispatchedRef = useRef(incomingValue)
  const inputType = String((p.inputType as string) || 'text')
  const changeStrategy = String(p.changeStrategy || (inputType === 'number' || inputType === 'date' ? 'immediate' : 'debounce'))
  const debounceMs = Math.max(0, Number(p.debounceMs ?? 180))
  const syncOnBlur = p.syncOnBlur !== false
  const { flush, schedule } = useDebouncedDispatcher<string>((nextValue) => {
    lastDispatchedRef.current = nextValue
    dispatch(nextValue)
  }, debounceMs)

  useEffect(() => {
    if (!localDirtyRef.current || incomingValue === lastDispatchedRef.current) {
      setValue(incomingValue)
      localDirtyRef.current = false
    }
  }, [incomingValue])

  const commitValue = useCallback((nextValue: string, immediate = false) => {
    localDirtyRef.current = true
    if (changeStrategy === 'blur' && !immediate) return
    if (immediate || changeStrategy === 'immediate') flush(nextValue)
    else schedule(nextValue)
  }, [changeStrategy, flush, schedule])

  const commonProps = {
    id: inputId,
    name: p.name as string,
    placeholder: (p.placeholder as string) || '',
    value,
    disabled: Boolean(p.disabled),
    'aria-busy': Boolean(p.loading),
    'aria-invalid': Boolean(p.error),
    'aria-describedby': p.error ? errorId : undefined,
    onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const nextValue = event.target.value
      setValue(nextValue)
      commitValue(nextValue)
    },
    onBlur: () => {
      if (syncOnBlur || changeStrategy === 'blur') {
        flush(value)
      }
    },
  }

  return (
    <div className={resolveMotionClass(p, ['bf-form-field'])} style={resolveMotionStyle(p)}>
      {p.label && <label className="bf-label" htmlFor={inputId}>{p.label as string}</label>}
      {p.loading ? <div className="bf-field-loading"><div className="bf-spinner bf-spinner-sm" /></div> : null}
      {inputType === 'textarea'
        ? <textarea {...commonProps} className="bf-textarea" />
        : <input {...commonProps} className={`bf-input${p.error ? ' error' : ''}`} type={inputType} />
      }
      {p.error && <span className="bf-input-error" id={errorId}>{p.error as string}</span>}
    </div>
  )
}

function DateRangePickerComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: Record<string, string>) => void }) {
  const generatedId = useId()
  const rangeName = String(p.label || p.name || 'Date range')
  const startId = `${String(p.id || p.name || `bf-date-range-${generatedId}`)}-start`
  const endId = `${String(p.id || p.name || `bf-date-range-${generatedId}`)}-end`
  const [start, setStart] = useState((p.start as string) || '')
  const [end, setEnd] = useState((p.end as string) || '')

  useEffect(() => {
    setStart((p.start as string) || '')
    setEnd((p.end as string) || '')
  }, [p.start, p.end])

  const emit = (nextStart: string, nextEnd: string) => dispatch({ start: nextStart, end: nextEnd })

  return (
    <div className={resolveMotionClass(p, ['bf-form-field', p.loading ? 'bf-is-loading' : ''])} style={resolveMotionStyle(p)}>
      {p.label && <label className="bf-label">{p.label as string}</label>}
      {p.loading ? <div className="bf-field-loading"><div className="bf-spinner bf-spinner-sm" /></div> : null}
      <div className="bf-date-range">
        <input
          id={startId}
          className="bf-input"
          type="date"
          name={`${p.name as string}_start`}
          aria-label={`${rangeName} start`}
          value={start}
          disabled={Boolean(p.disabled) || Boolean(p.loading)}
          onChange={(e) => {
            const next = e.target.value
            setStart(next)
            emit(next, end)
          }}
        />
        <span className="bf-date-range-sep">to</span>
        <input
          id={endId}
          className="bf-input"
          type="date"
          name={`${p.name as string}_end`}
          aria-label={`${rangeName} end`}
          value={end}
          disabled={Boolean(p.disabled) || Boolean(p.loading)}
          onChange={(e) => {
            const next = e.target.value
            setEnd(next)
            emit(start, next)
          }}
        />
      </div>
    </div>
  )
}

function MultiSelectComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: string[]) => void }) {
  const incomingValues = ((p.values as string[]) || []).map(String)
  const [selectedValues, setSelectedValues] = useState<string[]>(incomingValues)
  const options = (p.options as Array<{ label: string; value: string }>) || []

  useEffect(() => {
    setSelectedValues(incomingValues)
  }, [p.values])

  const toggleValue = (value: string) => {
    const selected = new Set(selectedValues)
    if (selected.has(value)) selected.delete(value)
    else selected.add(value)
    const next = Array.from(selected)
    setSelectedValues(next)
    dispatch(next)
  }

  return (
    <div className={resolveMotionClass(p, ['bf-form-field', p.loading ? 'bf-is-loading' : ''])} style={resolveMotionStyle(p)}>
      {p.label && <label className="bf-label">{p.label as string}</label>}
      {p.loading ? <div className="bf-field-loading"><div className="bf-spinner bf-spinner-sm" /></div> : null}
      <div className="bf-multiselect">
        {selectedValues.map((value) => (
          <input key={`hidden-${value}`} type="hidden" name={p.name as string} value={value} />
        ))}
        {!selectedValues.length && p.placeholder ? <div className="bf-multiselect-placeholder">{p.placeholder as string}</div> : null}
        {options.map((option) => {
          const active = selectedValues.includes(option.value)
          return (
            <button
              key={option.value}
              type="button"
              className={`bf-multiselect-chip ${active ? 'active' : ''}`}
              disabled={Boolean(p.disabled) || Boolean(p.loading)}
              onClick={() => toggleValue(option.value)}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function SidebarComponent({ props: p, children, ctx }: { props: Record<string, any>; children: VNodeData[]; ctx: RenderCtx }) {
  const activePath = window.location.pathname
  const [mobileOpen, setMobileOpen] = useState(false)
  const closeSidebar = () => setMobileOpen(false)

  return (
    <>
      <div className="bf-mobile-nav">
        <button type="button" className="bf-mobile-nav-toggle" onClick={() => setMobileOpen((open) => !open)}>
          <Icon name="LayoutDashboard" size={16} />
          <span className="bf-mobile-nav-copy">
            <strong>{p.brandName as string}</strong>
            {p.tagline ? <small>{p.tagline as string}</small> : null}
          </span>
        </button>
      </div>
      {mobileOpen ? <button type="button" className="bf-sidebar-backdrop" onClick={closeSidebar} aria-label="Close navigation" /> : null}
      <aside className={`bf-sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="bf-sidebar-brand">
          {p.logo
            ? <img src={p.logo as string} alt="logo" width={28} height={28} style={{ borderRadius: 6 }} />
            : <div className="bf-sidebar-brand-logo">{((p.brandName as string) || 'B').charAt(0)}</div>
          }
          <div className="bf-sidebar-brand-copy">
            <span className="bf-sidebar-brand-name">{p.brandName as string}</span>
            {p.tagline ? <span className="bf-sidebar-brand-tagline">{p.tagline as string}</span> : null}
          </div>
          <button type="button" className="bf-sidebar-close" onClick={closeSidebar} aria-label="Close navigation">
            <Icon name="X" size={16} />
          </button>
        </div>
        <nav className="bf-nav-section">
          {children.map((child, index) => {
            const cp = child.props as Record<string, any>
            const isActive = activePath === (cp.path as string)
            return (
              <button
                key={`${cp.path as string}-${index}`}
                className={`bf-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  closeSidebar()
                  ctx.navigate(cp.path as string)
                }}
              >
                {cp.icon ? <span className="bf-nav-icon"><Icon name={cp.icon as string} size={16} /></span> : null}
                {cp.label as string}
                {cp.badge ? <span className="bf-nav-badge">{cp.badge as string}</span> : null}
              </button>
            )
          })}
        </nav>
        {Boolean(p.showThemeToggle) ? (
          <div className="bf-sidebar-footer">
            <ThemeToggleComponent props={{ label: 'Theme', lightLabel: 'Light', darkLabel: 'Dark' }} ctx={ctx} />
          </div>
        ) : null}
      </aside>
    </>
  )
}

function TopNavComponent({ props: p, children, ctx }: { props: Record<string, any>; children: VNodeData[]; ctx: RenderCtx }) {
  const activePath = window.location.pathname
  const [mobileOpen, setMobileOpen] = useState(false)
  const actions = (p.actions as VNodeData[]) || []

  return (
    <header className={`bf-topnav ${p.sticky !== false ? 'sticky' : ''}`}>
      <div className="bf-topnav-inner">
        <div className="bf-topnav-brand">
          {p.logo ? <img className="bf-topnav-logo" src={p.logo as string} alt={String(p.brandName || 'Brand')} /> : <div className="bf-sidebar-brand-logo">{String((p.brandName as string) || 'B').charAt(0)}</div>}
          <div className="bf-topnav-copy">
            <span className="bf-topnav-brand-name">{p.brandName as string}</span>
            {p.tagline ? <span className="bf-topnav-brand-tagline">{p.tagline as string}</span> : null}
          </div>
        </div>
        <nav className="bf-topnav-links">
          {children.map((child, index) => {
            const cp = child.props as Record<string, any>
            const isActive = activePath === (cp.path as string)
            return (
              <button key={`${cp.path as string}-${index}`} type="button" className={`bf-topnav-link ${isActive ? 'active' : ''}`} onClick={() => ctx.navigate(cp.path as string)}>
                {cp.icon ? <Icon name={cp.icon as string} size={14} /> : null}
                <span>{cp.label as string}</span>
                {cp.badge ? <span className="bf-nav-badge">{cp.badge as string}</span> : null}
              </button>
            )
          })}
        </nav>
        <div className="bf-topnav-actions">
          {Boolean(p.showThemeToggle) ? <ThemeToggleComponent props={{ label: 'Theme', lightLabel: 'Light', darkLabel: 'Dark' }} ctx={ctx} /> : null}
          {actions.length ? renderChildren(actions, ctx, 'topnav-actions') : null}
          <button type="button" className="bf-topnav-menu" onClick={() => setMobileOpen((open) => !open)} aria-label="Toggle navigation menu">
            <Icon name={mobileOpen ? 'X' : 'LayoutDashboard'} size={16} />
          </button>
        </div>
      </div>
      {mobileOpen ? (
        <div className="bf-topnav-mobile">
          <div className="bf-topnav-mobile-panel">
            {children.map((child, index) => {
              const cp = child.props as Record<string, any>
              const isActive = activePath === (cp.path as string)
              return (
                <button
                  key={`mobile-${cp.path as string}-${index}`}
                  type="button"
                  className={`bf-topnav-mobile-link ${isActive ? 'active' : ''}`}
                  onClick={() => {
                    setMobileOpen(false)
                    ctx.navigate(cp.path as string)
                  }}
                >
                  {cp.icon ? <Icon name={cp.icon as string} size={15} /> : null}
                  <span>{cp.label as string}</span>
                  {cp.badge ? <span className="bf-nav-badge">{cp.badge as string}</span> : null}
                </button>
              )
            })}
            {actions.length ? <div className="bf-topnav-mobile-actions">{renderChildren(actions, ctx, 'topnav-mobile-actions')}</div> : null}
          </div>
        </div>
      ) : null}
    </header>
  )
}

function FormComponent({ props: p, children, ctx, nodeKey }: { props: Record<string, any>; children: VNodeData[]; ctx: RenderCtx; nodeKey: string }) {
  const [submitting, setSubmitting] = useState(false)

  const csrfToken = typeof document !== 'undefined'
    ? document.cookie
        .split('; ')
        .find((entry) => entry.startsWith('brickflowui_csrf='))
        ?.split('=')
        .slice(1)
        .join('=')
    : undefined

  return (
    <form
      className={`bf-form ${submitting ? 'bf-is-loading' : ''}`}
      onSubmit={async (e) => {
        e.preventDefault()
        setSubmitting(true)
        try {
          const data: Record<string, unknown> = {}
          new FormData(e.currentTarget).forEach((v, k) => {
            if (k in data) {
              const current = data[k]
              if (Array.isArray(current)) current.push(v)
              else data[k] = [current, v]
            } else {
              data[k] = v
            }
          })
          const resp = await fetch(p.action as string, {
            method: (p.method as string) || 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              ...(csrfToken ? { 'X-Brickflow-Csrf': decodeURIComponent(csrfToken) } : {}),
            },
            body: JSON.stringify(data),
          })
          if (resp.ok && p.successRedirect) {
            if (p.reloadOnSuccess) {
              window.location.assign(p.successRedirect as string)
            } else {
              ctx.navigate(p.successRedirect as string)
            }
          }
        } finally {
          setSubmitting(false)
        }
      }}
    >
      <fieldset className="bf-form-fieldset" disabled={submitting}>
        {renderChildren(children, ctx, nodeKey)}
      </fieldset>
    </form>
  )
}

function AccordionComponent({ props: p, children, ctx, nodeKey }: { props: Record<string, any>; children: VNodeData[]; ctx: RenderCtx; nodeKey: string }) {
  const defaultOpen = ((p.defaultOpen as number[]) || []).map(Number)
  const [openItems, setOpenItems] = useState<number[]>(defaultOpen)
  const allowMultiple = Boolean(p.allowMultiple)

  const toggle = (index: number) => {
    setOpenItems((prev) => {
      if (prev.includes(index)) return prev.filter((item) => item !== index)
      if (allowMultiple) return [...prev, index]
      return [index]
    })
  }

  return (
    <div className="bf-accordion">
      {children.map((child, index) => {
        const cp = child.props as Record<string, any>
        const open = openItems.includes(index)
        return (
          <div key={`${nodeKey}-${index}`} className={`bf-accordion-item ${open ? 'open' : ''}`}>
            <button type="button" className="bf-accordion-trigger" onClick={() => toggle(index)}>
              <div className="bf-accordion-trigger-main">
                {cp.icon ? <Icon name={cp.icon as string} size={15} /> : null}
                <div>
                  <div className="bf-accordion-title">{cp.title as string}</div>
                  {cp.subtitle ? <div className="bf-accordion-subtitle">{cp.subtitle as string}</div> : null}
                </div>
              </div>
              <span className="bf-accordion-chevron">{open ? '−' : '+'}</span>
            </button>
            {open ? <div className="bf-accordion-content">{renderChildren(child.children, ctx, `${nodeKey}-accordion-${index}`)}</div> : null}
          </div>
        )
      })}
    </div>
  )
}

function SparklineStatComponent({ props: p }: { props: Record<string, any> }) {
  const color = (p.color as string) || 'var(--db-primary)'
  return (
    <div className="bf-sparkline-stat">
      <div className="bf-sparkline-header">
        <div className="bf-stat-label">{p.label as string}</div>
        {p.delta ? <div className={`bf-stat-delta ${((p.deltaType as string) || 'neutral')}`}>{p.delta as string}</div> : null}
      </div>
      <div className="bf-stat-value">{p.value as string}</div>
      <div className="bf-sparkline-chart">
        <ResponsiveContainer width="100%" height={70}>
          <LineChart data={(p.data as object[]) || []}>
            <Line dataKey={p.yKey as string} stroke={color} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function GaugeChartComponent({ props: p }: { props: Record<string, any> }) {
  const min = Number(p.min ?? 0)
  const max = Number(p.max ?? 100)
  const value = Number(p.value ?? 0)
  const pct = Math.max(0, Math.min(1, (value - min) / Math.max(1, max - min)))
  const degrees = -90 + pct * 180

  return chartShell(String(p.title || 'gauge'), p,
    <div className="bf-gauge" style={{ minHeight: (p.height as number) || 220 }}>
      <div className="bf-gauge-arc">
        <div className="bf-gauge-fill" style={{ '--bf-gauge-pct': pct, background: (p.color as string) || 'var(--db-primary)' } as React.CSSProperties} />
        <div className="bf-gauge-needle" style={{ transform: `rotate(${degrees}deg)` }} />
      </div>
      <div className="bf-gauge-value">{value.toLocaleString()}</div>
      {p.label ? <div className="bf-gauge-label">{p.label as string}</div> : null}
    </div>
  )
}

function HeatmapComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: Record<string, unknown>) => void }) {
  const data = (p.data as Array<Record<string, any>>) || []
  if (!data.length) return <div className="bf-chart-state">{(p.emptyMessage as string) || 'No heatmap data available'}</div>

  const xKey = p.xKey as string
  const yKey = p.yKey as string
  const valueKey = p.valueKey as string
  const xs = Array.from(new Set(data.map((row) => String(row[xKey] ?? ''))))
  const ys = Array.from(new Set(data.map((row) => String(row[yKey] ?? ''))))
  const max = Math.max(1, ...data.map((row) => Number(row[valueKey] ?? 0)))
  const lookup = new Map(data.map((row) => [`${row[xKey]}::${row[yKey]}`, row]))

  return chartShell('heatmap', p,
    <div className="bf-heatmap" style={{ '--bf-heatmap-cols': xs.length + 1 } as React.CSSProperties}>
      <div className="bf-heatmap-corner" />
      {xs.map((x) => <div key={`x-${x}`} className="bf-heatmap-axis">{x}</div>)}
      {ys.map((y) => (
        <React.Fragment key={`row-${y}`}>
          <div className="bf-heatmap-axis y">{y}</div>
          {xs.map((x) => {
            const row = lookup.get(`${x}::${y}`)
            const value = Number(row?.[valueKey] ?? 0)
            const alpha = Math.max(0.08, Math.min(0.9, value / max))
            return (
              <button
                key={`${x}-${y}`}
                type="button"
                className="bf-heatmap-cell"
                title={`${x} / ${y}: ${value}`}
                style={{ background: `color-mix(in srgb, ${(p.color as string) || 'var(--db-primary)'} ${Math.round(alpha * 100)}%, var(--db-surface))` }}
                onClick={() => row && dispatch(row)}
              >
                {value}
              </button>
            )
          })}
        </React.Fragment>
      ))}
    </div>
  )
}

function PipelineGraphComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: Record<string, unknown>) => void }) {
  const nodes = (p.nodes as Array<Record<string, any>>) || []
  const edges = (p.edges as Array<Record<string, any>>) || []
  const vertical = p.layout === 'top-to-bottom'
  if (!nodes.length) return <div className="bf-chart-state">{(p.emptyMessage as string) || 'No pipeline nodes available'}</div>

  return (
    <div className={`bf-pipeline ${vertical ? 'vertical' : 'horizontal'} ${p.animated ? 'animated' : ''}`}>
      {p.title ? <div className="bf-chart-title">{p.title as string}</div> : null}
      <div className="bf-pipeline-canvas">
        {nodes.map((node, index) => {
          const incoming = edges.filter((edge) => edge.to === node.id).length
          const outgoing = edges.filter((edge) => edge.from === node.id).length
          const tone = statusTone(node.status)
          return (
            <React.Fragment key={String(node.id ?? index)}>
              <button type="button" className={`bf-pipeline-node ${tone}`} onClick={() => dispatch(node)}>
                <span className="bf-pipeline-node-layer">{String(node.layer ?? node.type ?? 'step')}</span>
                <span className="bf-pipeline-node-title">{String(node.label ?? node.id ?? '')}</span>
                <span className="bf-pipeline-node-meta">{String(node.status ?? 'unknown')}</span>
                <span className="bf-pipeline-node-flow">{incoming} in / {outgoing} out</span>
              </button>
              {index < nodes.length - 1 ? <div className={`bf-pipeline-edge ${p.animated ? 'pulse' : ''}`} /> : null}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

function StatusStripComponent({ props: p }: { props: Record<string, any> }) {
  const items = (p.items as Array<Record<string, any>>) || []
  return (
    <div className={resolveMotionClass(p, ['bf-status-strip'])} style={resolveMotionStyle(p)}>
      {p.title ? <div className="bf-card-title">{p.title as string}</div> : null}
      <div className="bf-status-strip-grid" style={{ '--bf-status-cols': Number(p.columns || 4) } as React.CSSProperties}>
        {items.map((item, index) => {
          const tone = statusTone(item.status || item.tone)
          return (
            <div key={index} className={`bf-signal-card ${tone}`}>
              <div className="bf-signal-label">{String(item.label ?? '')}</div>
              <div className="bf-signal-value">{String(item.value ?? '')}</div>
              {item.detail ? <div className="bf-signal-detail">{String(item.detail)}</div> : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function StepperComponent({ props: p }: { props: Record<string, any> }) {
  const steps = (p.steps as Array<Record<string, any>>) || []
  const active = Number(p.active || 0)
  return (
    <div className={resolveMotionClass(p, [`bf-stepper`, `bf-stepper-${(p.orientation as string) || 'horizontal'}`])} style={resolveMotionStyle(p)}>
      {steps.map((step, index) => {
        const state = index < active ? 'complete' : index === active ? 'active' : 'pending'
        return (
          <div key={index} className={`bf-stepper-step ${state}`}>
            <div className="bf-stepper-dot">{index + 1}</div>
            <div>
              <div className="bf-stepper-title">{String(step.label ?? step.title ?? '')}</div>
              {step.description ? <div className="bf-stepper-description">{String(step.description)}</div> : null}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function KanbanBoardComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: (v: Record<string, unknown>) => void }) {
  const columns = (p.columns as Array<Record<string, any>>) || []
  return (
    <div className={resolveMotionClass(p, ['bf-kanban'])} style={resolveMotionStyle(p)}>
      {columns.map((column, columnIndex) => {
        const cards = (column.cards as Array<Record<string, any>>) || []
        return (
          <div key={String(column.id ?? columnIndex)} className="bf-kanban-column">
            <div className="bf-kanban-header">
              <span>{String(column.label ?? column.title ?? '')}</span>
              <span className="bf-kanban-count">{cards.length}</span>
            </div>
            <div className="bf-kanban-cards">
              {cards.map((card, cardIndex) => (
                <button key={String(card.id ?? cardIndex)} type="button" className={`bf-kanban-card ${statusTone(card.status)}`} onClick={() => dispatch({ ...card, column: column.id ?? column.label })}>
                  <span className="bf-kanban-card-title">{String(card.title ?? '')}</span>
                  {card.subtitle ? <span className="bf-kanban-card-subtitle">{String(card.subtitle)}</span> : null}
                  {card.status ? <span className="bf-kanban-card-status">{String(card.status)}</span> : null}
                </button>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ChatMessageComponent({ props: p }: { props: Record<string, any> }) {
  const role = (p.role as string) || 'assistant'
  return (
    <div className={resolveMotionClass(p, [`bf-chat-message`, role, statusTone(p.tone)])} style={resolveMotionStyle(p)}>
      <div className="bf-chat-avatar">{p.avatar ? String(p.avatar) : role.slice(0, 1).toUpperCase()}</div>
      <div className="bf-chat-bubble">
        <div className="bf-chat-meta">
          <span>{String(p.name ?? role)}</span>
          {p.timestamp ? <span>{String(p.timestamp)}</span> : null}
        </div>
        <div className="bf-chat-content">{String(p.content ?? '')}</div>
      </div>
    </div>
  )
}

function ChatInputComponent({ props: p, dispatchChange, dispatchSubmit }: { props: Record<string, any>; dispatchChange: (v: string) => void; dispatchSubmit: (v: string) => void }) {
  const incomingValue = String((p.value as string) || '')
  const [value, setValue] = useState(incomingValue)
  const localDirtyRef = useRef(false)
  const lastDispatchedRef = useRef(incomingValue)
  const changeStrategy = String(p.changeStrategy || 'debounce')
  const debounceMs = Math.max(0, Number(p.debounceMs ?? 180))
  const { flush, schedule } = useDebouncedDispatcher<string>((nextValue) => {
    lastDispatchedRef.current = nextValue
    dispatchChange(nextValue)
  }, debounceMs)

  useEffect(() => {
    if (!localDirtyRef.current || incomingValue === lastDispatchedRef.current) {
      setValue(incomingValue)
      localDirtyRef.current = false
    }
  }, [incomingValue])

  const commitValue = useCallback((nextValue: string, immediate = false) => {
    localDirtyRef.current = true
    if (changeStrategy === 'blur' && !immediate) return
    if (immediate || changeStrategy === 'immediate') flush(nextValue)
    else schedule(nextValue)
  }, [changeStrategy, flush, schedule])

  const submit = () => {
    const next = value.trim()
    if (!next || p.disabled || p.loading) return
    flush(value)
    dispatchSubmit(next)
  }

  return (
    <div className={resolveMotionClass(p, ['bf-chat-input'])} style={resolveMotionStyle(p)}>
      <input
        className="bf-input"
        name={(p.name as string) || 'message'}
        value={value}
        placeholder={(p.placeholder as string) || 'Ask a question'}
        disabled={Boolean(p.disabled)}
        onChange={(event) => {
          const nextValue = event.target.value
          setValue(nextValue)
          commitValue(nextValue)
        }}
        onBlur={() => flush(value)}
        onKeyDown={(event) => {
          if (shouldSubmitChatInput(event.key, event.nativeEvent.isComposing)) {
            event.preventDefault()
            submit()
          }
        }}
      />
      <button type="button" className="bf-btn bf-btn-primary" disabled={Boolean(p.disabled) || Boolean(p.loading) || !value.trim()} onClick={submit}>
        {p.loading ? <span className="bf-spinner bf-spinner-sm" /> : null}
        {(p.submitLabel as string) || 'Send'}
      </button>
    </div>
  )
}

function tableCellTone(row: Record<string, unknown>, col: Record<string, any>, fallback: unknown) {
  const keyedTone = col.toneKey ? row[String(col.toneKey)] : undefined
  return statusTone(keyedTone ?? fallback ?? col.color)
}

function renderTableCell(row: Record<string, unknown>, col: Record<string, any>) {
  const rawValue = row[col.key]
  const format = String(col.format || 'text')

  if (format === 'badge' || format === 'status') {
    const tone = tableCellTone(row, col, rawValue)
    return <span className={`bf-table-pill ${tone}`}>{String(rawValue ?? '')}</span>
  }

  if (format === 'progress') {
    const value = Number(rawValue ?? 0)
    const max = Number(col.max ?? 100)
    const pct = Math.max(0, Math.min(100, (value / Math.max(1, max)) * 100))
    return (
      <div className="bf-table-progress">
        <div className="bf-table-progress-track">
          <div className={`bf-table-progress-fill ${tableCellTone(row, col, rawValue)}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="bf-table-progress-value">{String(col.suffix ? `${value}${col.suffix}` : value)}</span>
      </div>
    )
  }

  if (format === 'currency') {
    const value = Number(rawValue ?? 0)
    return <span>{new Intl.NumberFormat(undefined, { style: 'currency', currency: String(col.currency || 'USD'), maximumFractionDigits: 0 }).format(value)}</span>
  }

  if (format === 'metric') {
    return <span className="bf-table-metric">{String(rawValue ?? '')}</span>
  }

  if (format === 'image' || format === 'avatar') {
    const src = String(rawValue ?? '')
    if (!src) return <span className="bf-table-empty-cell">—</span>
    return (
      <img
        className={`bf-table-media ${format === 'avatar' ? 'avatar' : ''}`}
        src={src}
        alt={String(col.alt || col.label || 'media')}
      />
    )
  }

  return String(rawValue ?? '')
}

function TableComponent({ props: p, dispatch }: { props: Record<string, any>; dispatch: RenderCtx['dispatch'] }) {
  const data = (p.data as Record<string, unknown>[]) || []
  const columns = (p.columns as Array<Record<string, any>>) || []
  const pageSize = (p.pagination as number) || 20
  const [page, setPage] = useState(0)
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  let sorted = [...data]
  if (sortKey) {
    sorted.sort((a, b) => {
      const av = String(a[sortKey] ?? '')
      const bv = String(b[sortKey] ?? '')
      return sortDir === 'asc' ? av.localeCompare(bv, undefined, { numeric: true }) : bv.localeCompare(av, undefined, { numeric: true })
    })
  }

  const totalPages = Math.ceil(sorted.length / pageSize)
  const pageData = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
    setPage(0)
  }

  const exportCsv = () => {
    const csv = serializeCsv(
      columns.map(column => ({ label: column.label, key: String(column.key) })),
      sorted,
    )
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'brickflowui-table-export.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  if (p.loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
      <div className="bf-spinner bf-spinner-lg" />
    </div>
  )

  if (p.errorMessage) return (
    <div className="bf-table-empty">{p.errorMessage as string}</div>
  )

  if (!data.length) return (
    <div className="bf-table-empty">{p.emptyMessage as string || 'No data'}</div>
  )

  return (
    <div>
      {p.exportable && (
        <div className="bf-table-toolbar">
          <button type="button" className="bf-btn bf-btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={exportCsv}>
            Export CSV
          </button>
        </div>
      )}
      <div className="bf-table-wrapper">
        <table className="bf-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key} onClick={() => col.sortable && handleSort(col.key)}>
                  {col.label}
                  {col.sortable && sortKey === col.key && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.map((row, ri) => {
              const rowClickId = (p as Record<string, unknown>).rowClick as string
              return (
                <tr key={ri} className={rowClickId ? 'clickable' : ''} onClick={() => rowClickId && dispatch(rowClickId, { row })}>
                  {columns.map(col => (
                    <td key={col.key as string} title={String(row[col.key as string] ?? '')} className={col.align ? `bf-table-align-${String(col.align)}` : ''}>
                      {renderTableCell(row, col)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="bf-table-pagination">
          <span>Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, data.length)} of {data.length}</span>
          <div className="bf-table-pagination-controls">
            <button className="bf-btn bf-btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }} disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Prev</button>
            <button className="bf-btn bf-btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }} disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}

function TabsComponent({ props: p, children, ctx, nodeKey, dispatch }: { props: Record<string, any>; children: VNodeData[]; ctx: RenderCtx; nodeKey: string; dispatch: RenderCtx['dispatch'] }) {
  const generatedId = useId()
  const [active, setActive] = useState((p.defaultActive as number) || 0)

  useEffect(() => {
    setActive((p.defaultActive as number) || 0)
  }, [p.defaultActive])

  return (
    <div className={resolveMotionClass(p, ['bf-tabs'])} style={resolveMotionStyle(p)}>
      <div className="bf-tabs-list" role="tablist">
        {children.map((child, i) => {
          const cp = child.props as Record<string, unknown>
          return (
            <button key={i} type="button" role="tab" id={`${generatedId}-tab-${i}`} aria-selected={active === i} aria-controls={`${generatedId}-panel-${i}`} tabIndex={active === i ? 0 : -1} className={`bf-tab-trigger ${active === i ? 'active' : ''}`} onClick={() => {
              setActive(i)
              const changeId = p.change as string
              if (changeId) dispatch(changeId, { index: i })
            }}>
              {cp.icon ? <Icon name={cp.icon as string} size={14} /> : null}
              {cp.label as string}
            </button>
          )
        })}
      </div>
      <div className="bf-tab-content" role="tabpanel" id={`${generatedId}-panel-${active}`} aria-labelledby={`${generatedId}-tab-${active}`}>
        {children[active]?.children && renderChildren(children[active].children, ctx, `${nodeKey}-tab-${active}`)}
      </div>
    </div>
  )
}
