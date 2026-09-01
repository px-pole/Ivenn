import { useEffect, useState } from 'react'
import { AlertTriangle, Archive, CheckCircle2, FileSpreadsheet, FileText, LoaderCircle, RotateCcw, Upload } from 'lucide-react'
import { chooseBackupForRestore, fetchRestoreStatus, generateAndSaveFile, isTauri, relaunchForRestore, type RestoreStatus } from './api'

type Operation = 'csv' | 'pdf' | 'backup'

const actions: Array<{
  kind: Operation
  title: string
  description: string
  button: string
  icon: typeof Archive
}> = [
  { kind: 'csv', title: 'Spreadsheet export', description: 'A portable table of active inventory items for further analysis.', button: 'Save CSV', icon: FileSpreadsheet },
  { kind: 'pdf', title: 'Insurance-ready report', description: 'A printable room-by-room report with values and item photos.', button: 'Save PDF', icon: FileText },
  { kind: 'backup', title: 'Complete local backup', description: 'A consistent SQLite snapshot with all uploaded photos, receipts, and documents.', button: 'Save backup', icon: Archive },
]

export function DataView() {
  const [busy, setBusy] = useState<Operation | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [restoreStatus, setRestoreStatus] = useState<RestoreStatus | null>(null)
  const [restoreStaged, setRestoreStaged] = useState(false)

  useEffect(() => {
    fetchRestoreStatus().then((status) => {
      if (status) setRestoreStatus(status)
    }).catch(() => undefined)
  }, [])

  async function run(kind: Operation) {
    setBusy(kind)
    setMessage(null)
    setError(null)
    try {
      const saved = await generateAndSaveFile(kind)
      setMessage(saved ? 'File saved successfully.' : 'Save cancelled.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not generate this file.')
    } finally {
      setBusy(null)
    }
  }

  async function chooseRestore() {
    setError(null)
    try {
      setRestoreStaged(await chooseBackupForRestore())
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not stage this backup.')
    }
  }

  return (
    <section className="data-view">
      <div className="data-intro"><p className="eyebrow">Portable records</p><h2>Export and protect your data</h2><p>Reports include active inventory. A backup preserves the complete local database and every attachment.</p></div>
      <div className="data-actions">
        {actions.map((action) => {
          const Icon = action.icon
          return (
            <article className="data-action" key={action.kind}>
              <div className="data-icon"><Icon size={23} /></div>
              <div><h3>{action.title}</h3><p>{action.description}</p></div>
              <button className="secondary-button" type="button" disabled={busy !== null} onClick={() => void run(action.kind)}>{busy === action.kind ? <LoaderCircle className="spin" size={17} /> : <Icon size={17} />}{busy === action.kind ? 'Preparing...' : action.button}</button>
            </article>
          )
        })}
      </div>
      {message && <p className="data-message success"><CheckCircle2 size={17} />{message}</p>}
      {error && <p className="data-message error" role="alert">{error}</p>}
      {restoreStatus && <p className={`data-message ${restoreStatus.status}`} role={restoreStatus.status === 'error' ? 'alert' : undefined}>{restoreStatus.status === 'success' ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />}{restoreStatus.message}{restoreStatus.status === 'success' && restoreStatus.item_count !== null ? ` (${restoreStatus.item_count} items, ${restoreStatus.attachment_count ?? 0} attachments)` : ''}</p>}
      <div className="restore-panel">
        <div><AlertTriangle size={20} /><div><h3>Restore from backup</h3><p>Restoring replaces the current inventory and attachments after the app restarts.</p></div></div>
        {restoreStaged ? <button className="danger-action" type="button" onClick={() => void relaunchForRestore()}><RotateCcw size={17} />Restart and restore</button> : <button className="small-button" type="button" disabled={!isTauri} title={isTauri ? 'Choose an Inventory Vault backup' : 'Available in the desktop app'} onClick={() => void chooseRestore()}><Upload size={17} />Choose backup</button>}
      </div>
      <p className="backup-note">Keep backups somewhere separate from this computer. Restore validates file paths, checksums, and SQLite integrity before replacing current data.</p>
    </section>
  )
}
