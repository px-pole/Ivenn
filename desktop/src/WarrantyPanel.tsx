import { useEffect, useState } from 'react'
import { Check, Plus, ShieldCheck, Trash2, X } from 'lucide-react'
import { createWarranty, deleteWarranty, fetchWarranty, updateWarranty, type Warranty } from './api'

type Props = {
  itemId: string
  onChanged: () => Promise<void>
}

const emptyForm = { provider: '', expiresOn: '', policyNumber: '', notes: '' }

export function WarrantyPanel({ itemId, onChanged }: Props) {
  const [warranty, setWarranty] = useState<Warranty | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchWarranty(itemId, controller.signal)
      .then((result) => {
        setWarranty(result)
        if (result) setForm({ provider: result.provider ?? '', expiresOn: result.expires_on, policyNumber: result.policy_number ?? '', notes: result.notes ?? '' })
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof Error ? requestError.message : 'Could not load warranty details.')
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [itemId])

  async function save() {
    setBusy(true)
    setError(null)
    const payload = {
      provider: form.provider.trim() || null,
      expires_on: form.expiresOn,
      policy_number: form.policyNumber.trim() || null,
      notes: form.notes.trim() || null,
    }

    try {
      const saved = warranty ? await updateWarranty(itemId, payload) : await createWarranty(itemId, payload)
      setWarranty(saved)
      setEditing(false)
      await onChanged()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not save this warranty.')
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    setError(null)
    try {
      await deleteWarranty(itemId)
      setWarranty(null)
      setForm(emptyForm)
      setConfirmDelete(false)
      await onChanged()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not remove this warranty.')
    } finally {
      setBusy(false)
    }
  }

  const daysUntilExpiry = warranty ? Math.ceil((new Date(`${warranty.expires_on}T00:00:00`).getTime() - new Date().setHours(0, 0, 0, 0)) / 86_400_000) : null

  return (
    <section className="warranty-panel" aria-labelledby="warranty-title">
      <div className="warranty-heading">
        <div><h3 id="warranty-title">Warranty</h3><p>Coverage details and expiry</p></div>
        {!warranty && !editing && <button className="small-button" type="button" onClick={() => setEditing(true)}><Plus size={16} />Add warranty</button>}
      </div>

      {loading ? <p className="panel-message">Loading warranty...</p> : editing ? (
        <div className="warranty-form">
          <div className="form-grid">
            <label>Provider<input maxLength={150} value={form.provider} onChange={(event) => setForm((current) => ({ ...current, provider: event.target.value }))} /></label>
            <label>Expiry date<input required type="date" value={form.expiresOn} onChange={(event) => setForm((current) => ({ ...current, expiresOn: event.target.value }))} /></label>
            <label className="full-field">Policy or reference number<input maxLength={100} value={form.policyNumber} onChange={(event) => setForm((current) => ({ ...current, policyNumber: event.target.value }))} /></label>
            <label className="full-field">Notes<textarea maxLength={1000} rows={3} value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} /></label>
          </div>
          <div className="inline-actions"><button className="small-button" type="button" disabled={busy || !form.expiresOn} onClick={() => void save()}><Check size={16} />{busy ? 'Saving...' : 'Save warranty'}</button><button className="icon-button" type="button" title="Cancel warranty edit" onClick={() => setEditing(false)}><X size={17} /></button></div>
        </div>
      ) : warranty ? (
        <div className="warranty-summary">
          <div className={`warranty-mark ${daysUntilExpiry !== null && daysUntilExpiry < 0 ? 'expired' : daysUntilExpiry !== null && daysUntilExpiry <= 30 ? 'expiring' : ''}`}><ShieldCheck size={20} /></div>
          <div><strong>{warranty.provider || 'Warranty coverage'}</strong><span>Expires {new Date(`${warranty.expires_on}T00:00:00`).toLocaleDateString()}</span>{warranty.policy_number && <small>Reference: {warranty.policy_number}</small>}</div>
          <button className="small-button" type="button" onClick={() => setEditing(true)}>Edit</button>
          {confirmDelete ? <><button className="icon-button danger-button confirm-delete" type="button" title="Confirm remove warranty" disabled={busy} onClick={() => void remove()}><Trash2 size={16} /></button><button className="icon-button" type="button" title="Cancel removal" onClick={() => setConfirmDelete(false)}><X size={16} /></button></> : <button className="icon-button danger-button" type="button" title="Remove warranty" onClick={() => setConfirmDelete(true)}><Trash2 size={16} /></button>}
        </div>
      ) : <div className="panel-message"><ShieldCheck size={17} />No warranty recorded</div>}
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  )
}
