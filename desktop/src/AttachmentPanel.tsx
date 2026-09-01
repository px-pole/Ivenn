import { useEffect, useRef, useState } from 'react'
import { Download, FileScan, Paperclip, Plus, Sparkles, Trash2 } from 'lucide-react'
import {
  attachmentUrl,
  deleteAttachment,
  extractAttachment,
  fetchAttachments,
  uploadAttachment,
  type Attachment,
  type FieldSuggestion,
  type ReceiptExtraction,
} from './api'
import { AppSelect } from './AppSelect'

type Props = {
  itemId: string
  onApply: (suggestions: ReceiptExtraction) => void
}

const attachmentLabels: Record<Attachment['attachment_type'], string> = {
  item_photo: 'Item photo',
  receipt: 'Receipt',
  warranty_document: 'Warranty',
  other: 'Other',
}

export function AttachmentPanel({ itemId, onApply }: Props) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [attachmentType, setAttachmentType] = useState<Attachment['attachment_type']>('receipt')
  const [busy, setBusy] = useState(false)
  const [scanningId, setScanningId] = useState<string | null>(null)
  const [extraction, setExtraction] = useState<ReceiptExtraction | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchAttachments(itemId, controller.signal)
      .then(setAttachments)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof Error ? requestError.message : 'Could not load attachments.')
      })
    return () => controller.abort()
  }, [itemId])

  async function scan(attachment: Attachment) {
    setScanningId(attachment.id)
    setError(null)
    try {
      setExtraction(await extractAttachment(itemId, attachment.id))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not scan this receipt.')
    } finally {
      setScanningId(null)
    }
  }

  async function upload(file: File) {
    setBusy(true)
    setError(null)
    try {
      const attachment = await uploadAttachment(itemId, file, attachmentType)
      setAttachments((current) => [...current, attachment].sort((left, right) => left.file_name.localeCompare(right.file_name)))
      if (attachmentType === 'receipt' && attachment.mime_type.startsWith('image/')) await scan(attachment)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not upload this file.')
    } finally {
      setBusy(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  async function remove(attachment: Attachment) {
    setBusy(true)
    setError(null)
    try {
      await deleteAttachment(itemId, attachment.id)
      setAttachments((current) => current.filter((candidate) => candidate.id !== attachment.id))
      setExtraction(null)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not delete this attachment.')
    } finally {
      setBusy(false)
    }
  }

  const suggestions: Array<[string, FieldSuggestion]> = []
  if (extraction?.merchant) suggestions.push(['Merchant', extraction.merchant])
  if (extraction?.purchase_date) suggestions.push(['Purchase date', extraction.purchase_date])
  if (extraction?.estimated_value) suggestions.push(['Estimated value', extraction.estimated_value])
  if (extraction?.model) suggestions.push(['Model', extraction.model])
  if (extraction?.serial_number) suggestions.push(['Serial number', extraction.serial_number])

  return (
    <section className="attachment-panel" aria-labelledby="attachments-title">
      <div className="attachment-heading">
        <div><h3 id="attachments-title">Attachments</h3><p>Photos, receipts, and warranty documents</p></div>
        <div className="attachment-upload">
          <AppSelect ariaLabel="Attachment type" value={attachmentType} onChange={(value) => setAttachmentType(value as Attachment['attachment_type'])} options={Object.entries(attachmentLabels).map(([value, label]) => ({ value, label }))} />
          <input ref={fileInput} hidden type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file) }} />
          <button className="small-button" type="button" disabled={busy} onClick={() => fileInput.current?.click()}><Plus size={16} />Add file</button>
        </div>
      </div>

      {attachments.length === 0 ? (
        <div className="attachment-empty"><Paperclip size={18} />No files attached</div>
      ) : (
        <div className="attachment-list">
          {attachments.map((attachment) => (
            <div className="attachment-row" key={attachment.id}>
              <FileScan size={18} />
              <div><strong>{attachment.file_name}</strong><span>{attachmentLabels[attachment.attachment_type]}</span></div>
              {attachment.attachment_type === 'receipt' && attachment.mime_type.startsWith('image/') && <button className="icon-button" type="button" title={`Scan ${attachment.file_name}`} disabled={scanningId === attachment.id} onClick={() => void scan(attachment)}><Sparkles size={16} /></button>}
              <a className="icon-button" href={attachmentUrl(itemId, attachment.id)} title={`Download ${attachment.file_name}`}><Download size={16} /></a>
              <button className="icon-button danger-button" type="button" title={`Delete ${attachment.file_name}`} disabled={busy} onClick={() => void remove(attachment)}><Trash2 size={16} /></button>
            </div>
          ))}
        </div>
      )}

      {scanningId && <p className="scan-status"><Sparkles size={15} />Scanning receipt locally...</p>}
      {extraction && (
        <div className="extraction-review">
          <div><strong>Suggested values</strong><span>Review before applying to this item.</span></div>
          {suggestions.length ? <dl>{suggestions.map(([label, suggestion]) => <div key={label}><dt>{label}</dt><dd>{suggestion.value}<span>{Math.round(suggestion.confidence * 100)}%</span></dd></div>)}</dl> : <p>No structured values were recognised. The original file is still attached.</p>}
          {suggestions.length > 0 && <button className="small-button ai-button" type="button" onClick={() => { onApply(extraction); setExtraction(null) }}><Sparkles size={16} />Apply suggestions</button>}
        </div>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  )
}
