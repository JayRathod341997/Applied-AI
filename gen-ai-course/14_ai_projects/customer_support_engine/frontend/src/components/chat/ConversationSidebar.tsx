import { useNavigate } from 'react-router-dom'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { IssueTypeBadge } from '@/components/shared/IssueTypeBadge'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { StatusChip } from '@/components/shared/StatusChip'
import { useHistoryStore } from '@/store/historyStore'
import { useConversation } from '@/hooks/useConversation'
import { ROUTES } from '@/constants/routes'
import { truncate, formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { StoredConversation } from '@/types/conversation'

export function ConversationSidebar() {
  const conversations = useHistoryStore((s) => s.conversations)
  const { loadConversation, activeConversation } = useConversation()
  const navigate = useNavigate()

  const handleSelect = (conv: StoredConversation) => {
    loadConversation(conv)
    void navigate(ROUTES.CHAT)
  }

  if (conversations.length === 0) return null

  return (
    <div className="w-72 border-r flex flex-col bg-card shrink-0">
      <div className="px-4 py-3 border-b">
        <p className="text-sm font-medium">Conversations</p>
        <p className="text-xs text-muted-foreground">{conversations.length} total</p>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col">
          {conversations.map((conv, idx) => (
            <div key={conv.id}>
              <button
                onClick={() => handleSelect(conv)}
                className={cn(
                  'w-full flex flex-col gap-1.5 px-4 py-3 text-left hover:bg-accent transition-colors',
                  activeConversation?.id === conv.id && 'bg-primary/5'
                )}
              >
                <p className="text-xs text-foreground leading-snug line-clamp-2">
                  {truncate(conv.firstMessage, 72)}
                </p>
                <div className="flex items-center gap-1 flex-wrap">
                  <IssueTypeBadge issueType={conv.issueType} />
                  <SeverityBadge severity={conv.severity} />
                  <StatusChip status={conv.status} />
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(conv.updatedAt)} · {conv.messageCount} msgs
                </span>
              </button>
              {idx < conversations.length - 1 && <Separator />}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
