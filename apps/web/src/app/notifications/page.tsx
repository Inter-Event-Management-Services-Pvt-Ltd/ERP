'use client'

import { formatDistanceToNow } from 'date-fns'
import { Bell, BellOff } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useNotifications, useMarkNotificationRead } from '@/hooks/use-notifications'
import { apiErrorMessage } from '@/lib/errors'
import type { Notification } from '@/types'

function NotificationRow({ notification }: { notification: Notification }) {
  const mutation = useMarkNotificationRead()
  const isUnread = !notification.read_at

  return (
    <div
      className={`flex items-start gap-4 px-4 py-4 rounded-lg border transition-colors ${
        isUnread
          ? 'border-accent-saffron/20 bg-accent-saffron/5'
          : 'border-surface-border bg-surface-raised'
      }`}
    >
      <div
        className={`mt-1 flex-none w-2 h-2 rounded-full ${
          isUnread ? 'bg-accent-saffron' : 'bg-transparent border border-surface-border'
        }`}
        aria-hidden="true"
      />

      <div className="flex-1 min-w-0">
        <p
          className={`text-sm ${
            isUnread ? 'font-medium text-text-primary' : 'text-text-primary/70'
          }`}
        >
          {notification.title}
        </p>
        <p className="mt-0.5 text-xs text-text-primary/50 leading-relaxed">
          {notification.message}
        </p>
        <div className="mt-1.5 flex items-center gap-3 text-[10px] font-mono text-text-primary/30">
          <span>{formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}</span>
          {notification.notification_type && (
            <span className="uppercase tracking-wide">{notification.notification_type}</span>
          )}
        </div>
        {mutation.error && (
          <p role="alert" className="mt-1 text-xs text-accent-critical">
            {apiErrorMessage(mutation.error)}
          </p>
        )}
      </div>

      {isUnread && (
        <button
          type="button"
          onClick={() => mutation.mutate(notification.id)}
          disabled={mutation.isPending}
          aria-label={`Mark "${notification.title}" as read`}
          className="flex-none text-xs text-text-primary/30 hover:text-accent-saffron transition-colors disabled:opacity-40 whitespace-nowrap"
        >
          {mutation.isPending ? 'Marking…' : 'Mark read'}
        </button>
      )}
    </div>
  )
}

export default function NotificationsPage() {
  const { data: notifications, isLoading, error, refetch } = useNotifications({ limit: 100 })

  const unreadCount = (notifications ?? []).filter((n) => !n.read_at).length

  return (
    <AppShell>
      <PageHeader
        title="Notifications"
        subtitle={
          unreadCount > 0
            ? `${unreadCount} unread`
            : notifications && notifications.length > 0
            ? 'All caught up'
            : undefined
        }
      />
      <ContentArea>
        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState
            message={apiErrorMessage(error)}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && notifications?.length === 0 && (
          <EmptyState
            icon={BellOff}
            heading="No notifications"
            body="You're all caught up. New notifications will appear here."
          />
        )}

        {!isLoading && !error && notifications && notifications.length > 0 && (
          <div className="flex flex-col gap-2 max-w-2xl">
            {notifications.map((n) => (
              <NotificationRow key={n.id} notification={n} />
            ))}
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
