import { useDeferredValue, useState } from 'react'
import { Boxes, Plus, Search, X } from 'lucide-react'
import type { InventoryItem, NamedResource, WarrantyOverview } from './api'
import { AppSelect } from './AppSelect'

type Props = {
  items: InventoryItem[]
  rooms: NamedResource[]
  categories: NamedResource[]
  warranties: WarrantyOverview[]
  loading: boolean
  search: string
  onSearchChange: (value: string) => void
  onAdd: () => void
  onSelect: (item: InventoryItem) => void
}

export function ItemsView({ items, rooms, categories, warranties, loading, search, onSearchChange, onAdd, onSelect }: Props) {
  const [roomFilter, setRoomFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [warrantyFilter, setWarrantyFilter] = useState('')
  const deferredSearch = useDeferredValue(search.trim().toLocaleLowerCase())
  const roomNames = new Map(rooms.map((room) => [room.id, room.name]))
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]))
  const warrantiesByItem = new Map(warranties.map((warranty) => [warranty.item_id, warranty]))
  const visibleItems = items.filter((item) => {
    if (deferredSearch && ![item.name, item.brand, item.model, item.serial_number].some((value) => value?.toLocaleLowerCase().includes(deferredSearch))) return false
    if (roomFilter && item.room_id !== roomFilter) return false
    if (categoryFilter && item.category_id !== categoryFilter) return false
    if (statusFilter && item.status !== statusFilter) return false
    const warranty = warrantiesByItem.get(item.id)
    if (warrantyFilter === 'active' && (!warranty || warranty.days_until_expiry < 0)) return false
    if (warrantyFilter === 'expired' && (!warranty || warranty.days_until_expiry >= 0)) return false
    if (warrantyFilter === 'none' && warranty) return false
    return true
  })
  const filtersActive = Boolean(roomFilter || categoryFilter || statusFilter || warrantyFilter)

  function clearFilters() {
    setRoomFilter('')
    setCategoryFilter('')
    setStatusFilter('')
    setWarrantyFilter('')
    onSearchChange('')
  }

  return (
    <section className="items-view">
      <div className="items-controls">
        <label className="search items-search"><Search size={17} /><input type="search" value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Search name, brand, model, or serial" aria-label="Search items" /></label>
        <span>{visibleItems.length} {visibleItems.length === 1 ? 'item' : 'items'}</span>
      </div>
      <div className="item-filters" aria-label="Item filters">
        <AppSelect ariaLabel="Filter by room" value={roomFilter} onChange={setRoomFilter} options={[{ value: '', label: 'All rooms' }, ...rooms.map((room) => ({ value: room.id, label: room.name }))]} />
        <AppSelect ariaLabel="Filter by category" value={categoryFilter} onChange={setCategoryFilter} options={[{ value: '', label: 'All categories' }, ...categories.map((category) => ({ value: category.id, label: category.name }))]} />
        <AppSelect ariaLabel="Filter by status" value={statusFilter} onChange={setStatusFilter} options={[{ value: '', label: 'All statuses' }, { value: 'active', label: 'Active' }, { value: 'sold', label: 'Sold' }, { value: 'donated', label: 'Donated' }, { value: 'disposed', label: 'Disposed' }]} />
        <AppSelect ariaLabel="Filter by warranty" value={warrantyFilter} onChange={setWarrantyFilter} options={[{ value: '', label: 'Any warranty' }, { value: 'active', label: 'Covered' }, { value: 'expired', label: 'Expired' }, { value: 'none', label: 'No warranty' }]} />
        {(filtersActive || search) && <button className="filter-clear" type="button" onClick={clearFilters}><X size={15} />Clear</button>}
      </div>

      {loading ? (
        <div className="empty-state"><p>Loading inventory...</p></div>
      ) : visibleItems.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><Boxes size={27} /></div>
          <h3>{items.length ? 'No matching items' : 'Start building your inventory'}</h3>
          <p>{items.length ? 'Try a different name, brand, model, or serial number.' : 'Add the first item to begin tracking belongings, values, and warranty coverage.'}</p>
          {!items.length && <button className="secondary-button" type="button" onClick={onAdd}><Plus size={18} />Add your first item</button>}
        </div>
      ) : (
        <div className="item-table-wrap">
          <table className="item-table">
            <thead><tr><th>Item</th><th>Room</th><th>Category</th><th>Serial</th><th>Value</th><th>Status</th></tr></thead>
            <tbody>
              {visibleItems.map((item) => (
                <tr key={item.id}>
                  <td><button className="item-link" type="button" onClick={() => onSelect(item)}><strong>{item.name}</strong><span>{[item.brand, item.model].filter(Boolean).join(' / ') || 'No brand or model'}</span></button></td>
                  <td>{roomNames.get(item.room_id) ?? 'Unknown'}</td>
                  <td>{categoryNames.get(item.category_id) ?? 'Unknown'}</td>
                  <td>{item.serial_number || '—'}</td>
                  <td>{item.estimated_value ? Number(item.estimated_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}</td>
                  <td><span className={`status-badge ${item.status}`}>{item.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
