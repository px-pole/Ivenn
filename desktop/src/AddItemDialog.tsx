import { useEffect, useState, type FormEvent } from 'react'
import { Plus, X } from 'lucide-react'
import { createItem, type NamedResource } from './api'

type Props = {
  rooms: NamedResource[]
  categories: NamedResource[]
  onClose: () => void
  onCreated: () => Promise<void>
}

const initialForm = {
  name: '',
  roomName: '',
  categoryName: '',
  brand: '',
  model: '',
  serialNumber: '',
  estimatedValue: '',
  purchaseDate: '',
}

export function AddItemDialog({ rooms, categories, onClose, onCreated }: Props) {
  const [form, setForm] = useState(initialForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  function update(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)

    try {
      await createItem(form, rooms, categories)
      await onCreated()
      onClose()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not add the item.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="add-item-title">
        <header className="dialog-header">
          <div><p className="eyebrow">New inventory record</p><h2 id="add-item-title">Add item</h2></div>
          <button className="icon-button" type="button" title="Close" onClick={onClose}><X size={19} /></button>
        </header>
        <form onSubmit={(event) => void submit(event)}>
          <div className="form-grid">
            <label className="full-field">Item name<input autoFocus required maxLength={200} value={form.name} onChange={(event) => update('name', event.target.value)} /></label>
            <label>Room<input required list="room-options" maxLength={100} value={form.roomName} onChange={(event) => update('roomName', event.target.value)} placeholder="Choose or create" /></label>
            <label>Category<input required list="category-options" maxLength={100} value={form.categoryName} onChange={(event) => update('categoryName', event.target.value)} placeholder="Choose or create" /></label>
            <datalist id="room-options">{rooms.map((room) => <option key={room.id} value={room.name} />)}</datalist>
            <datalist id="category-options">{categories.map((category) => <option key={category.id} value={category.name} />)}</datalist>
            <label>Brand<input maxLength={100} value={form.brand} onChange={(event) => update('brand', event.target.value)} /></label>
            <label>Model<input maxLength={100} value={form.model} onChange={(event) => update('model', event.target.value)} /></label>
            <label>Serial number<input maxLength={100} value={form.serialNumber} onChange={(event) => update('serialNumber', event.target.value)} /></label>
            <label>Estimated value<input min="0" step="0.01" type="number" value={form.estimatedValue} onChange={(event) => update('estimatedValue', event.target.value)} /></label>
            <label>Purchase date<input type="date" value={form.purchaseDate} onChange={(event) => update('purchaseDate', event.target.value)} /></label>
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <footer className="dialog-actions">
            <button className="text-button" type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={saving}><Plus size={18} />{saving ? 'Adding...' : 'Add item'}</button>
          </footer>
        </form>
      </section>
    </div>
  )
}
