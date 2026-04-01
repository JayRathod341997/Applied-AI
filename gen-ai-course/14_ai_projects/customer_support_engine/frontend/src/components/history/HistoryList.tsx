import { useNavigate } from 'react-router-dom'
import { HistoryCard } from './HistoryCard'
import { HistorySearch } from './HistorySearch'
import { HistoryFilters } from './HistoryFilters'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversationHistory } from '@/hooks/useConversationHistory'
import { useConversation } from '@/hooks/useConversation'
import { useHistoryStore } from '@/store/historyStore'
import { ROUTES } from '@/constants/routes'
import { History } from 'lucide-react'

export function HistoryList() {
  const navigate = useNavigate()
  const { conversations, totalCount, searchQuery, setSearchQuery, filters, setFilters, clearFilters } =
    useConversationHistory()
  const { loadConversation } = useConversation()

  const handleOpen = (id: string) => {
    const conv = useHistoryStore.getState().getConversation(id)
    if (!conv) return
    loadConversation({
      id: conv.id,
      firstMessage: conv.firstMessage,
      messages: conv.messages,
      issueType: conv.issueType,
      severity: conv.severity,
      status: conv.status,
      messageCount: conv.messageCount,
      createdAt: conv.createdAt,
      updatedAt: conv.updatedAt,
    })
    void navigate(ROUTES.CHAT)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 p-4 border-b">
        <HistorySearch value={searchQuery} onChange={setSearchQuery} />
        <HistoryFilters filters={filters} onChange={setFilters} onClear={clearFilters} />
      </div>

      {/* Count */}
      <div className="px-4 py-2 border-b">
        <p className="text-xs text-muted-foreground">
          {conversations.length === totalCount
            ? `${totalCount} conversations`
            : `${conversations.length} of ${totalCount} conversations`}
        </p>
      </div>

      {/* List */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                <History className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium">No conversations found</p>
              <p className="text-xs text-muted-foreground">
                {totalCount === 0 ? 'Start a chat to see history here' : 'Try adjusting your search or filters'}
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {conversations.map((conv) => (
                <HistoryCard
                  key={conv.id}
                  conversation={conv}
                  onClick={() => handleOpen(conv.id)}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
