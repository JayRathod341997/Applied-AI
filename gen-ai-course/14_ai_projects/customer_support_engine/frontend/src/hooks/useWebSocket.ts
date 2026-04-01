import { useEffect, useRef, useCallback } from 'react'
import { SupportWebSocket } from '@/lib/websocket'
import { useConversationStore } from '@/store/conversationStore'
import { useHistoryStore } from '@/store/historyStore'
import { isWsError } from '@/types/api'
import type { WsStatus } from '@/types/conversation'
import type { Message } from '@/types/conversation'
import { generateId } from '@/lib/utils'

export function useWebSocket(conversationId: string | null) {
  const wsRef = useRef<SupportWebSocket | null>(null)

  // Select stable action references — never recreate these callbacks
  const setWsStatus = useConversationStore((s) => s.setWsStatus)
  const setIsTyping = useConversationStore((s) => s.setIsTyping)
  const appendMessage = useConversationStore((s) => s.appendMessage)
  const updateMeta = useConversationStore((s) => s.updateMeta)
  const upsertConversation = useHistoryStore((s) => s.upsertConversation)

  const handleMessage = useCallback(
    (data: Parameters<typeof isWsError>[0]) => {
      setIsTyping(false)

      if (isWsError(data)) {
        const errorMsg: Message = {
          id: generateId(),
          role: 'assistant',
          content: `Error: ${data.error}`,
          timestamp: new Date().toISOString(),
          isError: true,
        }
        appendMessage(errorMsg)
        return
      }

      const assistantMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: data.reply,
        timestamp: new Date().toISOString(),
        issueType: data.issue_type,
        severity: data.severity,
        status: data.status,
      }

      appendMessage(assistantMsg)
      updateMeta({
        issueType: data.issue_type,
        severity: data.severity,
        status: data.status,
      })

      const conv = useConversationStore.getState().activeConversation
      if (conv) {
        // conv already includes assistantMsg because appendMessage is sync
        upsertConversation({
          ...conv,
          messageCount: conv.messages.length,
          updatedAt: assistantMsg.timestamp,
        })
      }
    },
    [appendMessage, updateMeta, setIsTyping, upsertConversation]
  )

  const handleStatusChange = useCallback(
    (status: WsStatus) => setWsStatus(status),
    [setWsStatus]
  )

  useEffect(() => {
    if (!conversationId) return

    wsRef.current = new SupportWebSocket(conversationId, handleMessage, handleStatusChange)

    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [conversationId, handleMessage, handleStatusChange])

  const send = useCallback((message: string) => {
    wsRef.current?.send(message)
  }, [])

  return { send }
}
