import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Bell,
  Boxes,
  CircleAlert,
  Shapes,
  FolderOpen,
  House,
  Languages,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { AddItemDialog } from './AddItemDialog'
import { AppSelect } from './AppSelect'
import {
  fetchCategories,
  fetchItems,
  fetchNotifications,
  fetchRooms,
  fetchSummary,
  fetchWarranties,
  type InventoryItem,
  type InventorySummary,
  type InAppNotification,
  type NamedResource,
  type WarrantyOverview,
} from './api'
import { ItemsView } from './ItemsView'
import { ItemDetailsDialog } from './ItemDetailsDialog'
import { RoomsView } from './RoomsView'
import { WarrantiesView } from './WarrantiesView'
import { DataView } from './DataView'
import { CategoriesView } from './CategoriesView'
import { NotificationsPanel } from './NotificationsPanel'
import { useTheme } from './useTheme'
import './App.css'

const STARTUP_ATTEMPTS = 60
const STARTUP_RETRY_MS = 250

type View = 'overview' | 'items' | 'rooms' | 'categories' | 'warranties' | 'data'

function App() {
  const { t, i18n } = useTranslation()
  const activeLanguage = i18n.resolvedLanguage?.split('-')[0] ?? 'en'
  useTheme() // Initialize theme hook for system preference detection
  const [summary, setSummary] = useState<InventorySummary | null>(null)
  const [items, setItems] = useState<InventoryItem[]>([])
  const [rooms, setRooms] = useState<NamedResource[]>([])
  const [categories, setCategories] = useState<NamedResource[]>([])
  const [warranties, setWarranties] = useState<WarrantyOverview[]>([])
  const [notifications, setNotifications] = useState<InAppNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<View>('overview')
  const [search, setSearch] = useState('')
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null)
  const [showNotifications, setShowNotifications] = useState(false)

  async function refreshData() {
    const [nextSummary, nextItems, nextRooms, nextCategories, nextWarranties, nextNotifications] = await Promise.all([
      fetchSummary(),
      fetchItems(),
      fetchRooms(),
      fetchCategories(),
      fetchWarranties(),
      fetchNotifications(),
    ])
    setSummary(nextSummary)
    setItems(nextItems)
    setRooms(nextRooms)
    setCategories(nextCategories)
    setWarranties(nextWarranties)
    setNotifications(nextNotifications)
  }

  async function loadSummary() {
    setLoading(true)
    setError(null)

    try {
      await refreshData()
    } catch {
      setError(t('error.backendNotRunning'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()

    async function connectToBackend() {
      for (let attempt = 0; attempt < STARTUP_ATTEMPTS; attempt += 1) {
        try {
          await fetchSummary(controller.signal)
          return Promise.all([
            fetchSummary(controller.signal),
            fetchItems(controller.signal),
            fetchRooms(controller.signal),
            fetchCategories(controller.signal),
            fetchWarranties(controller.signal),
            fetchNotifications(controller.signal),
          ])
        } catch (requestError) {
          if (controller.signal.aborted) throw requestError
          await new Promise((resolve) => setTimeout(resolve, STARTUP_RETRY_MS))
        }
      }

      throw new Error('Backend startup timed out')
    }

    connectToBackend()
      .then(([nextSummary, nextItems, nextRooms, nextCategories, nextWarranties, nextNotifications]) => {
        setSummary(nextSummary)
        setItems(nextItems)
        setRooms(nextRooms)
        setCategories(nextCategories)
        setWarranties(nextWarranties)
        setNotifications(nextNotifications)
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(t('error.backendNotRunning'))
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [])

  useEffect(() => {
    document.documentElement.lang = activeLanguage
  }, [activeLanguage])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <div className="brand-logo">I</div>
          <span>{t('app.name')}</span>
        </div>
        <nav aria-label="Main navigation">
          <button className={`nav-item ${activeView === 'overview' ? 'active' : ''}`} type="button" onClick={() => setActiveView('overview')}><Boxes size={18} /><span>{t('nav.overview')}</span></button>
          <button className={`nav-item ${activeView === 'items' ? 'active' : ''}`} type="button" onClick={() => setActiveView('items')}><FolderOpen size={18} /><span>{t('nav.items')}</span></button>
          <button className={`nav-item ${activeView === 'rooms' ? 'active' : ''}`} type="button" onClick={() => setActiveView('rooms')}><House size={18} /><span>{t('nav.rooms')}</span></button>
          <button className={`nav-item ${activeView === 'categories' ? 'active' : ''}`} type="button" onClick={() => setActiveView('categories')}><Shapes size={18} /><span>{t('nav.categories')}</span></button>
          <button className={`nav-item ${activeView === 'warranties' ? 'active' : ''}`} type="button" onClick={() => setActiveView('warranties')}><ShieldCheck size={18} /><span>{t('nav.warranties')}</span></button>
        </nav>
        <div className="sidebar-language">
          <AppSelect ariaLabel={t('settings.language')} value={activeLanguage} onChange={(language) => void i18n.changeLanguage(language)} leadingIcon={<Languages size={16} />} options={[{ value: 'en', label: 'English' }, { value: 'de', label: 'Deutsch' }, { value: 'fr', label: 'Français' }, { value: 'es', label: 'Español' }]} />
        </div>
        <div className={`service-status ${error ? 'offline' : 'online'}`}>
          <span className="status-dot" />
          <div>
            <strong>{error ? t('app.status.offline') : t('app.status.online')}</strong>
            <span>{error ? t('app.status.offlineDesc') : t('app.status.onlineDesc')}</span>
          </div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">{t('header.eyebrow')}</p>
            <h1>
              {activeView === 'overview' && t('section.overview')}
              {activeView === 'items' && t('section.items')}
              {activeView === 'rooms' && t('section.rooms')}
              {activeView === 'categories' && t('section.categories')}
              {activeView === 'warranties' && t('section.warranties')}
              {activeView === 'data' && 'Data & exports'}
            </h1>
          </div>
          <div className="toolbar">
            {activeView === 'overview' && <label className="search"><Search size={17} /><input type="search" value={search} onChange={(event) => { setSearch(event.target.value); setActiveView('items') }} placeholder={t('header.search')} aria-label={t('header.search')} /></label>}
            <button className="icon-button notification-button" type="button" title={t('header.notifications')} aria-expanded={showNotifications} onClick={() => setShowNotifications((visible) => !visible)}><Bell size={19} />{notifications.some((notification) => !notification.is_read) && <span className="notification-dot" />}</button>
            {(activeView === 'overview' || activeView === 'items') && <button className="primary-button" type="button" onClick={() => setShowAddDialog(true)}><Plus size={18} />{t('action.addItem')}</button>}
          </div>
          {showNotifications && <NotificationsPanel notifications={notifications} onChanged={async () => setNotifications(await fetchNotifications())} onClose={() => setShowNotifications(false)} onOpenItem={(itemId) => { const item = items.find((candidate) => candidate.id === itemId); if (item) setSelectedItem(item); setShowNotifications(false) }} />}
        </header>

        {error && (
          <section className="connection-banner" aria-live="polite">
            <CircleAlert size={21} />
            <div><strong>{error}</strong><span>The managed local service did not start. Check the Tauri log, then reconnect.</span></div>
            <button type="button" onClick={() => void loadSummary()}><RefreshCw size={17} />Reconnect</button>
          </section>
        )}

        {activeView === 'overview' ? (
          <>
            <section className="stats" aria-label="Inventory summary">
              <article><span>{t('stats.totalItems')}</span><strong>{loading ? '...' : summary?.total_items ?? 0}</strong><small>{t('stats.totalItemsDesc')}</small></article>
              <article><span>{t('stats.activeItems')}</span><strong>{loading ? '...' : summary?.active_items ?? 0}</strong><small>{t('stats.activeItemsDesc')}</small></article>
              <article><span>{t('stats.rooms')}</span><strong>{loading ? '...' : summary?.rooms_count ?? 0}</strong><small>{t('stats.roomsDesc')}</small></article>
              <article><span>{t('stats.categories')}</span><strong>{loading ? '...' : summary?.categories_count ?? 0}</strong><small>{t('stats.categoriesDesc')}</small></article>
            </section>
            <section className="workspace">
              <div className="section-heading"><div><p className="eyebrow">{t('inventory.title')}</p><h2>{t('inventory.title')}</h2></div><button type="button" onClick={() => setActiveView('items')}>{t('action.viewAll')}</button></div>
              <div className="empty-state">
                <div className="empty-icon"><Boxes size={27} /></div>
                <h3>{items.length ? t('inventory.itemsRecorded', { count: items.length, itemLabel: items.length === 1 ? t('inventory.itemLabel') : t('inventory.itemsLabel') }) : t('inventory.empty')}</h3>
                <p>{items.length ? 'Open the Items view to search and review everything you have recorded.' : t('inventory.emptyLong')}</p>
                <button className="secondary-button" type="button" onClick={items.length ? () => setActiveView('items') : () => setShowAddDialog(true)}>{items.length ? <FolderOpen size={18} /> : <Plus size={18} />}{items.length ? t('action.viewAll') : t('action.addItem')}</button>
              </div>
            </section>
          </>
        ) : activeView === 'items' ? (
          <ItemsView items={items} rooms={rooms} categories={categories} warranties={warranties} loading={loading} search={search} onSearchChange={setSearch} onAdd={() => setShowAddDialog(true)} onSelect={setSelectedItem} />
        ) : activeView === 'rooms' ? (
          <RoomsView rooms={rooms} items={items} loading={loading} onChanged={refreshData} />
        ) : activeView === 'categories' ? (
          <CategoriesView categories={categories} items={items} loading={loading} onChanged={refreshData} />
        ) : activeView === 'warranties' ? (
          <WarrantiesView warranties={warranties} loading={loading} onSelectItem={(itemId) => { const item = items.find((candidate) => candidate.id === itemId); if (item) setSelectedItem(item) }} />
        ) : (
          <DataView />
        )}
      </main>
      {showAddDialog && <AddItemDialog rooms={rooms} categories={categories} onClose={() => setShowAddDialog(false)} onCreated={refreshData} />}
      {selectedItem && <ItemDetailsDialog item={selectedItem} rooms={rooms} categories={categories} onClose={() => setSelectedItem(null)} onSaved={refreshData} onDeleted={async () => { setSelectedItem(null); await refreshData() }} />}
    </div>
  )
}

export default App
