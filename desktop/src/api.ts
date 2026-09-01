export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8765/api/v1'

export type InventorySummary = {
  total_items: number
  active_items: number
  rooms_count: number
  categories_count: number
}

export type NamedResource = {
  id: string
  name: string
}

export type InventoryItem = {
  id: string
  user_id: string
  room_id: string
  category_id: string
  name: string
  brand: string | null
  model: string | null
  serial_number: string | null
  estimated_value: string | null
  purchase_date: string | null
  status: 'active' | 'sold' | 'donated' | 'disposed'
}

export type Attachment = {
  id: string
  item_id: string
  file_name: string
  mime_type: string
  attachment_type: 'item_photo' | 'receipt' | 'warranty_document' | 'other'
}

export type FieldSuggestion = {
  value: string
  confidence: number
  evidence: string
}

export type ReceiptExtraction = {
  raw_text: string
  merchant: FieldSuggestion | null
  purchase_date: FieldSuggestion | null
  estimated_value: FieldSuggestion | null
  model: FieldSuggestion | null
  serial_number: FieldSuggestion | null
}

export type Warranty = {
  id: string
  item_id: string
  provider: string | null
  expires_on: string
  policy_number: string | null
  notes: string | null
}

export type WarrantyOverview = Warranty & {
  item_name: string
  item_status: InventoryItem['status']
  days_until_expiry: number
}

export type GeneratedFile = {
  file_name: string
  download_path: string
}

export type RestoreStatus = {
  status: 'success' | 'error'
  message: string
  item_count: number | null
  attachment_count: number | null
}

export type InAppNotification = {
  id: string
  item_id: string
  item_name: string
  title: string
  message: string
  is_read: boolean
  created_at: string
}

export const isTauri = '__TAURI_INTERNALS__' in window

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function fetchSummary(signal?: AbortSignal) {
  return request<InventorySummary>('/reports/summary', { signal })
}

export function fetchItems(signal?: AbortSignal) {
  return request<InventoryItem[]>('/items', { signal })
}

export function fetchRooms(signal?: AbortSignal) {
  return request<NamedResource[]>('/rooms', { signal })
}

export function fetchCategories(signal?: AbortSignal) {
  return request<NamedResource[]>('/categories', { signal })
}

export function fetchWarranties(signal?: AbortSignal) {
  return request<WarrantyOverview[]>('/warranties', { signal })
}

export function fetchNotifications(signal?: AbortSignal) {
  return request<InAppNotification[]>('/notifications', { signal })
}

export function updateNotification(notificationId: string, input: { is_read?: boolean, is_dismissed?: boolean }) {
  return request<InAppNotification>(`/notifications/${notificationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function markAllNotificationsRead() {
  return request<{ updated_count: number }>('/notifications/mark-all-read', { method: 'POST' })
}

export async function fetchWarranty(itemId: string, signal?: AbortSignal) {
  const response = await fetch(`${API_URL}/items/${itemId}/warranty`, { signal })
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`)
  return response.json() as Promise<Warranty>
}

export function createWarranty(itemId: string, input: WarrantyInput) {
  return request<Warranty>(`/items/${itemId}/warranty`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function updateWarranty(itemId: string, input: WarrantyInput) {
  return request<Warranty>(`/items/${itemId}/warranty`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export async function deleteWarranty(itemId: string) {
  const response = await fetch(`${API_URL}/items/${itemId}/warranty`, { method: 'DELETE' })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
}

export type WarrantyInput = {
  provider: string | null
  expires_on: string
  policy_number: string | null
  notes: string | null
}

export function fetchAttachments(itemId: string, signal?: AbortSignal) {
  return request<Attachment[]>(`/items/${itemId}/attachments`, { signal })
}

export function uploadAttachment(itemId: string, file: File, attachmentType: Attachment['attachment_type']) {
  const body = new FormData()
  body.append('attachment_type', attachmentType)
  body.append('file', file)
  return request<Attachment>(`/items/${itemId}/attachments`, { method: 'POST', body })
}

export function extractAttachment(itemId: string, attachmentId: string) {
  return request<ReceiptExtraction>(`/items/${itemId}/attachments/${attachmentId}/extract`, { method: 'POST' })
}

export async function deleteAttachment(itemId: string, attachmentId: string) {
  const response = await fetch(`${API_URL}/items/${itemId}/attachments/${attachmentId}`, { method: 'DELETE' })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
}

export function attachmentUrl(itemId: string, attachmentId: string) {
  return `${API_URL}/items/${itemId}/attachments/${attachmentId}`
}

export async function generateAndSaveFile(kind: 'csv' | 'pdf' | 'backup') {
  const path = kind === 'backup' ? '/maintenance/backup' : `/maintenance/export/${kind}`
  const artifact = await request<GeneratedFile>(path, { method: 'POST' })

  if (isTauri) {
    const { invoke } = await import('@tauri-apps/api/core')
    return invoke<boolean>('save_generated_file', { fileName: artifact.file_name })
  }

  const response = await fetch(`${API_URL}${artifact.download_path}`)
  if (!response.ok) throw new Error(`Download failed with status ${response.status}`)
  const objectUrl = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = artifact.file_name
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  return true
}

export function fetchRestoreStatus() {
  return request<RestoreStatus | null>('/maintenance/restore-status')
}

export async function chooseBackupForRestore() {
  if (!isTauri) throw new Error('Restore is available in the desktop app')
  const { invoke } = await import('@tauri-apps/api/core')
  return invoke<boolean>('stage_restore')
}

export async function relaunchForRestore() {
  if (!isTauri) throw new Error('Restore is available in the desktop app')
  const { relaunch } = await import('@tauri-apps/plugin-process')
  await relaunch()
}

export function createRoom(name: string) {
  return request<NamedResource>('/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim() }),
  })
}

export function createCategory(name: string) {
  return request<NamedResource>('/categories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim() }),
  })
}

export function renameCategory(categoryId: string, name: string) {
  return request<NamedResource>(`/categories/${categoryId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim() }),
  })
}

export async function deleteCategory(categoryId: string) {
  const response = await fetch(`${API_URL}/categories/${categoryId}`, { method: 'DELETE' })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
}

export function renameRoom(roomId: string, name: string) {
  return request<NamedResource>(`/rooms/${roomId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim() }),
  })
}

export async function deleteRoom(roomId: string) {
  const response = await fetch(`${API_URL}/rooms/${roomId}`, { method: 'DELETE' })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
}

async function findOrCreateResource(path: '/rooms' | '/categories', name: string, existing: NamedResource[]) {
  const normalizedName = name.trim()
  const match = existing.find((resource) => resource.name.toLocaleLowerCase() === normalizedName.toLocaleLowerCase())
  if (match) return match

  return request<NamedResource>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: normalizedName }),
  })
}

export async function createItem(input: {
  name: string
  roomName: string
  categoryName: string
  brand: string
  model: string
  serialNumber: string
  estimatedValue: string
  purchaseDate: string
}, rooms: NamedResource[], categories: NamedResource[]) {
  const room = await findOrCreateResource('/rooms', input.roomName, rooms)
  const category = await findOrCreateResource('/categories', input.categoryName, categories)

  return request<InventoryItem>('/items', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: input.name.trim(),
      room_id: room.id,
      category_id: category.id,
      brand: input.brand.trim() || null,
      model: input.model.trim() || null,
      serial_number: input.serialNumber.trim() || null,
      estimated_value: input.estimatedValue || null,
      purchase_date: input.purchaseDate || null,
    }),
  })
}

export async function updateItem(item: InventoryItem, input: {
  name: string
  roomId: string
  categoryId: string
  brand: string
  model: string
  serialNumber: string
  estimatedValue: string
  purchaseDate: string
  status: InventoryItem['status']
}) {
  const updatedItem = await request<InventoryItem>(`/items/${item.id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: input.name.trim(),
      room_id: input.roomId,
      category_id: input.categoryId,
      brand: input.brand.trim() || null,
      model: input.model.trim() || null,
      serial_number: input.serialNumber.trim() || null,
      estimated_value: input.estimatedValue || null,
      purchase_date: input.purchaseDate || null,
    }),
  })

  if (input.status === item.status) return updatedItem

  return request<InventoryItem>(`/items/${item.id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: input.status }),
  })
}

export async function deleteItem(itemId: string) {
  const response = await fetch(`${API_URL}/items/${itemId}`, { method: 'DELETE' })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
}
