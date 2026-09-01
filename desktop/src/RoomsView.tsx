import { useState, type FormEvent } from 'react'
import { Check, House, Pencil, Plus, Trash2, X } from 'lucide-react'
import { createRoom, deleteRoom, renameRoom, type InventoryItem, type NamedResource } from './api'

type Props = {
  rooms: NamedResource[]
  items: InventoryItem[]
  loading: boolean
  onChanged: () => Promise<void>
}

export function RoomsView({ rooms, items, loading, onChanged }: Props) {
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const itemCounts = new Map<string, number>()
  for (const item of items) itemCounts.set(item.room_id, (itemCounts.get(item.room_id) ?? 0) + 1)

  async function run(operation: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await operation()
      await onChanged()
      return true
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not update rooms.')
      return false
    } finally {
      setBusy(false)
    }
  }

  async function submitNewRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (await run(() => createRoom(newName))) {
      setNewName('')
      setShowCreate(false)
    }
  }

  async function saveRename(roomId: string) {
    if (await run(() => renameRoom(roomId, editingName))) setEditingId(null)
  }

  function beginRename(room: NamedResource) {
    setEditingId(room.id)
    setConfirmDeleteId(null)
    setEditingName(room.name)
    setError(null)
  }

  return (
    <section className="rooms-view">
      <div className="rooms-heading">
        <div><p className="eyebrow">Locations</p><h2>Manage rooms</h2><p>Organise items by where they are kept.</p></div>
        <button className="primary-button" type="button" onClick={() => setShowCreate(true)} disabled={showCreate}><Plus size={18} />Add room</button>
      </div>

      {showCreate && (
        <form className="room-create" onSubmit={(event) => void submitNewRoom(event)}>
          <label>Room name<input autoFocus required maxLength={100} value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="e.g. Kitchen" /></label>
          <button className="secondary-button" type="submit" disabled={busy}><Check size={17} />Create</button>
          <button className="icon-button" type="button" title="Cancel" onClick={() => { setShowCreate(false); setNewName(''); setError(null) }}><X size={18} /></button>
        </form>
      )}

      {error && <p className="form-error room-error" role="alert">{error}</p>}

      {loading ? (
        <div className="empty-state"><p>Loading rooms...</p></div>
      ) : rooms.length === 0 ? (
        <div className="empty-state"><div className="empty-icon"><House size={27} /></div><h3>No rooms yet</h3><p>Add a room to organise the first inventory item.</p></div>
      ) : (
        <div className="room-grid">
          {rooms.map((room) => {
            const itemCount = itemCounts.get(room.id) ?? 0
            const editing = editingId === room.id
            const confirmingDelete = confirmDeleteId === room.id
            return (
              <article className="room-row" key={room.id}>
                <div className="room-icon"><House size={20} /></div>
                <div className="room-info">
                  {editing ? (
                    <input autoFocus required maxLength={100} value={editingName} onChange={(event) => setEditingName(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void saveRename(room.id); if (event.key === 'Escape') setEditingId(null) }} />
                  ) : <strong>{room.name}</strong>}
                  <span>{itemCount} {itemCount === 1 ? 'item' : 'items'}</span>
                </div>
                <div className="room-actions">
                  {editing ? (
                    <><button className="icon-button" type="button" title="Save room name" disabled={busy || !editingName.trim()} onClick={() => void saveRename(room.id)}><Check size={17} /></button><button className="icon-button" type="button" title="Cancel rename" onClick={() => setEditingId(null)}><X size={17} /></button></>
                  ) : confirmingDelete ? (
                    <><button className="icon-button danger-button confirm-delete" type="button" title={`Confirm delete ${room.name}`} disabled={busy} onClick={() => void run(() => deleteRoom(room.id)).then((deleted) => { if (deleted) setConfirmDeleteId(null) })}><Trash2 size={16} /></button><button className="icon-button" type="button" title="Cancel delete" onClick={() => setConfirmDeleteId(null)}><X size={17} /></button></>
                  ) : (
                    <><button className="icon-button" type="button" title={`Rename ${room.name}`} onClick={() => beginRename(room)}><Pencil size={16} /></button><button className="icon-button danger-button" type="button" title={itemCount ? `Move ${itemCount} item(s) before deleting` : `Delete ${room.name}`} disabled={busy || itemCount > 0} onClick={() => setConfirmDeleteId(room.id)}><Trash2 size={16} /></button></>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
