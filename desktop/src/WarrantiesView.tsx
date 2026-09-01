import { CalendarClock, CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { WarrantyOverview } from './api'

type Props = {
  warranties: WarrantyOverview[]
  loading: boolean
  onSelectItem: (itemId: string) => void
}

function coverageState(days: number) {
  if (days < 0) return { label: 'Expired', className: 'expired' }
  if (days <= 30) return { label: days === 0 ? 'Expires today' : `${days} days left`, className: 'expiring' }
  return { label: 'Covered', className: 'covered' }
}

export function WarrantiesView({ warranties, loading, onSelectItem }: Props) {
  const expired = warranties.filter((warranty) => warranty.days_until_expiry < 0).length
  const expiring = warranties.filter((warranty) => warranty.days_until_expiry >= 0 && warranty.days_until_expiry <= 30).length
  const covered = warranties.filter((warranty) => warranty.days_until_expiry > 30).length

  return (
    <section className="warranties-view">
      <div className="warranty-stats" aria-label="Warranty summary">
        <article><ShieldAlert size={18} /><div><strong>{expired}</strong><span>Expired</span></div></article>
        <article><CalendarClock size={18} /><div><strong>{expiring}</strong><span>Due within 30 days</span></div></article>
        <article><CheckCircle2 size={18} /><div><strong>{covered}</strong><span>Covered beyond 30 days</span></div></article>
      </div>

      <div className="warranty-list-panel">
        <div className="section-heading"><div><p className="eyebrow">Coverage</p><h2>All warranties</h2></div><span>{warranties.length} {warranties.length === 1 ? 'record' : 'records'}</span></div>
        {loading ? <div className="empty-state"><p>Loading warranties...</p></div> : warranties.length === 0 ? (
          <div className="empty-state"><div className="empty-icon"><ShieldCheck size={27} /></div><h3>No warranties recorded</h3><p>Open an item to add provider, policy, and expiry details.</p></div>
        ) : (
          <div className="warranty-list">
            {warranties.map((warranty) => {
              const state = coverageState(warranty.days_until_expiry)
              return (
                <button className="warranty-row" type="button" key={warranty.id} onClick={() => onSelectItem(warranty.item_id)}>
                  <div className={`warranty-mark ${state.className}`}><ShieldCheck size={19} /></div>
                  <div><strong>{warranty.item_name}</strong><span>{warranty.provider || 'Provider not specified'}</span></div>
                  <div><strong>{new Date(`${warranty.expires_on}T00:00:00`).toLocaleDateString()}</strong><span>{warranty.policy_number || 'No reference number'}</span></div>
                  <span className={`warranty-badge ${state.className}`}>{state.label}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}
