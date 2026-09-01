import { Bell, CheckCheck, X } from 'lucide-react'
import { markAllNotificationsRead, updateNotification, type InAppNotification } from './api'

type Props = {
  notifications: InAppNotification[]
  onChanged: () => Promise<void>
  onClose: () => void
  onOpenItem: (itemId: string) => void
}

export function NotificationsPanel({ notifications, onChanged, onClose, onOpenItem }: Props) {
  async function open(notification: InAppNotification) {
    if (!notification.is_read) await updateNotification(notification.id, { is_read: true })
    await onChanged()
    onOpenItem(notification.item_id)
  }

  async function dismiss(notificationId: string) {
    await updateNotification(notificationId, { is_dismissed: true })
    await onChanged()
  }

  async function markAllRead() {
    await markAllNotificationsRead()
    await onChanged()
  }

  const unread = notifications.filter((notification) => !notification.is_read).length

  return (
    <section className="notifications-panel" aria-label="In-app notifications">
      <header>
        <div><strong>Notifications</strong><span>{unread ? `${unread} unread` : 'All caught up'}</span></div>
        <button className="icon-button" type="button" title="Close notifications" onClick={onClose}><X size={17} /></button>
      </header>
      {notifications.length === 0 ? <div className="notifications-empty"><Bell size={22} /><strong>No notifications</strong><span>Warranty reminders will appear here.</span></div> : <>
        <div className="notification-list">
          {notifications.map((notification) => <article className={notification.is_read ? 'read' : ''} key={notification.id}>
            <button className="notification-content" type="button" onClick={() => void open(notification)}><span className="notification-unread" /><div><strong>{notification.title}</strong><p>{notification.message}</p><small>{notification.item_name}</small></div></button>
            <button className="notification-dismiss" type="button" title={`Dismiss ${notification.item_name} notification`} onClick={() => void dismiss(notification.id)}><X size={15} /></button>
          </article>)}
        </div>
        {unread > 0 && <footer><button type="button" onClick={() => void markAllRead()}><CheckCheck size={16} />Mark all read</button></footer>}
      </>}
    </section>
  )
}
