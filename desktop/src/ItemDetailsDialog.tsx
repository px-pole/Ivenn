import { useEffect, useState, type FormEvent } from 'react'
import { Save, Trash2, X } from 'lucide-react'
import { AttachmentPanel } from './AttachmentPanel'
import { deleteItem, updateItem, type InventoryItem, type NamedResource } from './api'
import { AppSelect } from './AppSelect'
import { WarrantyPanel } from './WarrantyPanel'

type Props = {
  item: InventoryItem
  rooms: NamedResource[]
  categories: NamedResource[]
  onClose: () => void
  onSaved: () => Promise<void>
  onDeleted: () => Promise<void>
}

export function ItemDetailsDialog({ item, rooms, categories, onClose, onSaved, onDeleted }: Props) {
  const [form, setForm] = useState({
    name: item.name,
    roomId: item.room_id,
    categoryId: item.category_id,
    brand: item.brand ?? '',
    model: item.model ?? '',
    serialNumber: item.serial_number ?? '',
    estimatedValue: item.estimated_value ?? '',
    purchaseDate: item.purchase_date ?? '',
    status: item.status,
  })
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  function update<K extends keyof typeof form>(field: K, value: typeof form[K]) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)

    try {
      await updateItem(item, form)
      await onSaved()
      onClose()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not save this item.')
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    setSaving(true)
    setError(null)
    try {
      await deleteItem(item.id)
      await onDeleted()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not delete this item.')
      setSaving(false)
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="item-details-title">
        <header className="dialog-header">
          <div><p className="eyebrow">Inventory record</p><h2 id="item-details-title">Item details</h2></div>
          <button className="icon-button" type="button" title="Close" onClick={onClose}><X size={19} /></button>
        </header>
        <form onSubmit={(event) => void submit(event)}>
          <div className="form-grid">
            <label className="full-field">Item name<input autoFocus required maxLength={200} value={form.name} onChange={(event) => update('name', event.target.value)} /></label>
            <label>Room<AppSelect ariaLabel="Room" value={form.roomId} onChange={(value) => update('roomId', value)} options={rooms.map((room) => ({ value: room.id, label: room.name }))} /></label>
            <label>Category<AppSelect ariaLabel="Category" value={form.categoryId} onChange={(value) => update('categoryId', value)} options={categories.map((category) => ({ value: category.id, label: category.name }))} /></label>
            <label>Brand<input maxLength={100} value={form.brand} onChange={(event) => update('brand', event.target.value)} /></label>
            <label>Model<input maxLength={100} value={form.model} onChange={(event) => update('model', event.target.value)} /></label>
            <label>Serial number<input maxLength={100} value={form.serialNumber} onChange={(event) => update('serialNumber', event.target.value)} /></label>
            <label>Estimated value<input min="0" step="0.01" type="number" value={form.estimatedValue} onChange={(event) => update('estimatedValue', event.target.value)} /></label>
            <label>Purchase date<input type="date" value={form.purchaseDate} onChange={(event) => update('purchaseDate', event.target.value)} /></label>
            <label>Status<AppSelect ariaLabel="Status" value={form.status} onChange={(value) => update('status', value as InventoryItem['status'])} options={[{ value: 'active', label: 'Active' }, { value: 'sold', label: 'Sold' }, { value: 'donated', label: 'Donated' }, { value: 'disposed', label: 'Disposed' }]} /></label>
          </div>
          <AttachmentPanel
            itemId={item.id}
            onApply={(suggestions) => setForm((current) => ({
              ...current,
              model: suggestions.model?.value ?? current.model,
              serialNumber: suggestions.serial_number?.value ?? current.serialNumber,
              estimatedValue: suggestions.estimated_value?.value ?? current.estimatedValue,
              purchaseDate: suggestions.purchase_date?.value ?? current.purchaseDate,
            }))}
          />
          <WarrantyPanel itemId={item.id} onChanged={onSaved} />
          {error && <p className="form-error" role="alert">{error}</p>}
          <footer className="dialog-actions">
            {confirmDelete ? <><button className="danger-action" type="button" disabled={saving} onClick={() => void remove()}><Trash2 size={17} />Confirm delete</button><button className="text-button" type="button" onClick={() => setConfirmDelete(false)}>Keep item</button></> : <button className="delete-item-button" type="button" onClick={() => setConfirmDelete(true)}><Trash2 size={17} />Delete item</button>}
            <span className="dialog-action-spacer" />
            <button className="text-button" type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={saving}><Save size={18} />{saving ? 'Saving...' : 'Save changes'}</button>
          </footer>
        </form>
      </section>
    </div>
  )
}
