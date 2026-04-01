import { MessageSquare, History, BarChart3, Settings, Plus, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { DeleteConversationDialog } from '@/components/shared/DeleteConversationDialog'
import { SidebarItem } from './SidebarItem'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { IssueTypeBadge } from '@/components/shared/IssueTypeBadge'
import { StatusChip } from '@/components/shared/StatusChip'
import { useHistoryStore } from '@/store/historyStore'
import { useConversationStore } from '@/store/conversationStore'
import { ROUTES } from '@/constants/routes'
import { truncate, formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface Props {
  collapsed: boolean
}

const NAV_ITEMS = [
  { to: ROUTES.CHAT, icon: MessageSquare, label: 'Chat' },
  { to: ROUTES.HISTORY, icon: History, label: 'History' },
  { to: ROUTES.DASHBOARD, icon: BarChart3, label: 'Dashboard' },
  { to: ROUTES.SETTINGS, icon: Settings, label: 'Settings' },
]

export function Sidebar({ collapsed }: Props) {
  const navigate = useNavigate()
  // Select the full array — slice in render, not in selector (selector must return stable ref)
  const conversations = useHistoryStore((s) => s.conversations)
  const recentConversations = conversations.slice(0, 8)
  const reset = useConversationStore((s) => s.reset)

  const handleNewChat = () => {
    reset()
    void navigate(ROUTES.CHAT)
  }

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-200',
        collapsed ? 'w-14' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className={cn('flex items-center gap-2 px-4 py-4 border-b', collapsed && 'justify-center px-2')}>
        <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center shrink-0">
          <MessageSquare className="h-4 w-4 text-primary-foreground" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-semibold leading-none truncate">Support Engine</p>
            <p className="text-xs text-muted-foreground mt-0.5">AI-powered</p>
          </div>
        )}
      </div>

      {/* New Chat */}
      <div className={cn('p-3', collapsed && 'flex justify-center')}>
        <Button
          size={collapsed ? 'icon' : 'sm'}
          className="w-full gap-2"
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4 shrink-0" />
          {!collapsed && 'New Chat'}
        </Button>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex flex-col gap-1 p-2">
        {NAV_ITEMS.map((item) => (
          <SidebarItem key={item.to} {...item} collapsed={collapsed} />
        ))}
      </nav>

      <Separator />

      {/* Recent Conversations */}
      {!collapsed && recentConversations.length > 0 && (
        <div className="flex flex-col min-h-0 flex-1">
          <p className="text-xs font-medium text-muted-foreground px-4 py-2">Recent</p>
          <ScrollArea className="flex-1">
            <div className="flex flex-col gap-0.5 px-2 pb-2">
              {recentConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => void navigate(ROUTES.CHAT)}
                  className="group relative flex flex-col gap-1 rounded-md px-3 py-2 text-left hover:bg-accent transition-colors cursor-pointer"
                >
                  <div className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <DeleteConversationDialog conversation={conv}>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-muted-foreground hover:text-destructive shrink-0"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </DeleteConversationDialog>
                  </div>
                  <p className="text-xs text-foreground leading-snug pr-6">
                    {truncate(conv.firstMessage || (conv.messages && conv.messages[0]?.content) || 'New Conversation', 48)}
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <IssueTypeBadge issueType={conv.issueType} />
                    <StatusChip status={conv.status} />
                    <span className="text-xs text-muted-foreground ml-auto">
                      {formatRelativeTime(conv.updatedAt)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}
    </aside>
  )
}
