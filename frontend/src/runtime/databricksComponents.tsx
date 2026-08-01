import React from 'react'

type Props = Record<string, any>

function StateMessage({ kind, children }: { kind: 'status' | 'alert'; children: React.ReactNode }) {
  return (
    <div className={`bf-databricks-message bf-databricks-${kind}`} role={kind}>
      {children}
    </div>
  )
}

export function WarehouseSelectorView({
  props,
  onSelect,
}: {
  props: Props
  onSelect: (warehouseId: string) => void
}) {
  const warehouses = Array.isArray(props.warehouses) ? props.warehouses : []
  const label = String(props.label || 'SQL Warehouse')
  if (props.loading) return <StateMessage kind="status">Loading warehouses...</StateMessage>
  if (props.error) return <StateMessage kind="alert">{String(props.error)}</StateMessage>
  return (
    <label className="bf-form-field bf-databricks-selector">
      <span className="bf-label">{label}</span>
      <select
        className="bf-select"
        aria-label={label}
        value={String(props.selectedId || '')}
        disabled={Boolean(props.disabled) || warehouses.length === 0}
        onChange={(event) => onSelect(event.target.value)}
      >
        <option value="">{warehouses.length ? `Choose ${label.toLowerCase()}` : String(props.emptyMessage || 'No warehouses available')}</option>
        {warehouses.map((warehouse: Props) => (
          <option key={String(warehouse.id)} value={String(warehouse.id)}>
            {String(warehouse.name || warehouse.id)}{warehouse.state ? ` - ${String(warehouse.state)}` : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

export function CatalogBrowserView({
  props,
  onSelect,
}: {
  props: Props
  onSelect: (selection: Record<string, string>) => void
}) {
  const catalogs = Array.isArray(props.catalogs) ? props.catalogs : []
  const selected = (props.selected && typeof props.selected === 'object') ? props.selected : {}
  if (props.loading) return <StateMessage kind="status">Loading catalogs...</StateMessage>
  if (props.error) return <StateMessage kind="alert">{String(props.error)}</StateMessage>
  if (!catalogs.length) return <StateMessage kind="status">{String(props.emptyMessage || 'No catalogs available')}</StateMessage>
  return (
    <div className="bf-catalog-browser" aria-label="Unity Catalog browser">
      {catalogs.map((catalog: Props) => (
        <section key={String(catalog.name)} className="bf-catalog-group">
          <h3>{String(catalog.name)}</h3>
          {(Array.isArray(catalog.schemas) ? catalog.schemas : []).map((schema: Props) => (
            <div key={`${catalog.name}.${schema.name}`} className="bf-schema-group">
              <div className="bf-schema-name">{String(schema.name)}</div>
              <div className="bf-catalog-tables">
                {(Array.isArray(schema.tables) ? schema.tables : []).map((table: Props) => {
                  const fullName = String(table.full_name || `${catalog.name}.${schema.name}.${table.name}`)
                  const active = selected.catalog === catalog.name
                    && selected.schema === schema.name
                    && selected.table === table.name
                  return (
                    <button
                      key={fullName}
                      type="button"
                      className={`bf-catalog-table${active ? ' is-selected' : ''}`}
                      aria-pressed={active}
                      disabled={Boolean(props.disabled)}
                      onClick={() => {
                        if (!props.disabled) {
                          onSelect({
                            level: 'table',
                            catalog: String(catalog.name),
                            schema: String(schema.name),
                            table: String(table.name),
                            full_name: fullName,
                          })
                        }
                      }}
                    >
                      <span>{fullName}</span>
                      {table.table_type ? <small>{String(table.table_type)}</small> : null}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </section>
      ))}
    </div>
  )
}

export function JobTriggerView({
  props,
  onTrigger,
}: {
  props: Props
  onTrigger: (payload: Record<string, string>) => void
}) {
  const disabled = Boolean(props.disabled) || Boolean(props.loading)
  return (
    <div className="bf-job-trigger">
      <button
        type="button"
        className="bf-btn bf-btn-primary"
        disabled={disabled}
        onClick={() => {
          if (!disabled) onTrigger({ job_id: String(props.jobId) })
        }}
      >
        {props.loading ? <span className="bf-spinner bf-spinner-sm" /> : null}
        {String(props.label || 'Run Job')}
      </button>
      {props.status ? <span className={`bf-badge bf-badge-${String(props.status).toLowerCase()}`}>{String(props.status)}</span> : null}
      {props.runId ? <span className="bf-job-run-id">Run {String(props.runId)}</span> : null}
      {props.error ? <StateMessage kind="alert">{String(props.error)}</StateMessage> : null}
    </div>
  )
}
