import { useState, type FormEvent } from 'react'
import { Check, Pencil, Plus, Shapes, Trash2, X } from 'lucide-react'
import { createCategory, deleteCategory, renameCategory, type InventoryItem, type NamedResource } from './api'

type Props = {
  categories: NamedResource[]
  items: InventoryItem[]
  loading: boolean
  onChanged: () => Promise<void>
}

export function CategoriesView({ categories, items, loading, onChanged }: Props) {
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const itemCounts = new Map<string, number>()
  for (const item of items) itemCounts.set(item.category_id, (itemCounts.get(item.category_id) ?? 0) + 1)

  async function run(operation: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await operation()
      await onChanged()
      return true
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not update categories.')
      return false
    } finally {
      setBusy(false)
    }
  }

  async function submitNew(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (await run(() => createCategory(newName))) {
      setNewName('')
      setShowCreate(false)
    }
  }

  async function saveRename(categoryId: string) {
    if (await run(() => renameCategory(categoryId, editingName))) setEditingId(null)
  }

  return (
    <section className="rooms-view">
      <div className="rooms-heading">
        <div><p className="eyebrow">Classification</p><h2>Manage categories</h2><p>Group similar belongings for faster filtering and reports.</p></div>
        <button className="primary-button" type="button" onClick={() => setShowCreate(true)} disabled={showCreate}><Plus size={18} />Add category</button>
      </div>

      {showCreate && <form className="room-create" onSubmit={(event) => void submitNew(event)}><label>Category name<input autoFocus required maxLength={100} value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="e.g. Electronics" /></label><button className="secondary-button" type="submit" disabled={busy}><Check size={17} />Create</button><button className="icon-button" type="button" title="Cancel" onClick={() => { setShowCreate(false); setNewName(''); setError(null) }}><X size={18} /></button></form>}
      {error && <p className="form-error room-error" role="alert">{error}</p>}

      {loading ? <div className="empty-state"><p>Loading categories...</p></div> : categories.length === 0 ? <div className="empty-state"><div className="empty-icon"><Shapes size={27} /></div><h3>No categories yet</h3><p>Add a category to classify your inventory.</p></div> : (
        <div className="room-grid">
          {categories.map((category) => {
            const itemCount = itemCounts.get(category.id) ?? 0
            const editing = editingId === category.id
            const confirmingDelete = confirmDeleteId === category.id
            return <article className="room-row" key={category.id}>
              <div className="room-icon"><Shapes size={20} /></div>
              <div className="room-info">{editing ? <input autoFocus required maxLength={100} value={editingName} onChange={(event) => setEditingName(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void saveRename(category.id); if (event.key === 'Escape') setEditingId(null) }} /> : <strong>{category.name}</strong>}<span>{itemCount} {itemCount === 1 ? 'item' : 'items'}</span></div>
              <div className="room-actions">
                {editing ? <><button className="icon-button" type="button" title="Save category name" disabled={busy || !editingName.trim()} onClick={() => void saveRename(category.id)}><Check size={17} /></button><button className="icon-button" type="button" title="Cancel rename" onClick={() => setEditingId(null)}><X size={17} /></button></> : confirmingDelete ? <><button className="icon-button danger-button confirm-delete" type="button" title={`Confirm delete ${category.name}`} disabled={busy} onClick={() => void run(() => deleteCategory(category.id)).then((deleted) => { if (deleted) setConfirmDeleteId(null) })}><Trash2 size={16} /></button><button className="icon-button" type="button" title="Cancel delete" onClick={() => setConfirmDeleteId(null)}><X size={17} /></button></> : <><button className="icon-button" type="button" title={`Rename ${category.name}`} onClick={() => { setEditingId(category.id); setEditingName(category.name); setConfirmDeleteId(null); setError(null) }}><Pencil size={16} /></button><button className="icon-button danger-button" type="button" title={itemCount ? `Move ${itemCount} item(s) before deleting` : `Delete ${category.name}`} disabled={busy || itemCount > 0} onClick={() => setConfirmDeleteId(category.id)}><Trash2 size={16} /></button></>}
              </div>
            </article>
          })}
        </div>
      )}
    </section>
  )
}
