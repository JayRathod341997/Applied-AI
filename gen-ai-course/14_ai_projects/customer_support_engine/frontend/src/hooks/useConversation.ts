import { useState, useCallback, useRef } from 'react'
import { supportApi } from '@/lib/api'
import { useConversationStore } from '@/store/conversationStore'
import { useHistoryStore } from '@/store/historyStore'
import { useWebSocket } from './useWebSocket'
import { generateId } from '@/lib/utils'
import type { Message } from '@/types/conversation'

export function useConversation() {
  // Select stable action references individually — avoids creating a new object on every render
  const activeConversation = useConversationStore((s) => s.activeConversation)
  const wsStatus = useConversationStore((s) => s.wsStatus)
  const isTyping = useConversationStore((s) => s.isTyping)
  const error = useConversationStore((s) => s.error)
  const startConversation = useConversationStore((s) => s.startConversation)
  const appendMessage = useConversationStore((s) => s.appendMessage)
  const updateMeta = useConversationStore((s) => s.updateMeta)
  const setIsTyping = useConversationStore((s) => s.setIsTyping)
  const setError = useConversationStore((s) => s.setError)
  const reset = useConversationStore((s) => s.reset)
  const loadConversationAction = useConversationStore((s) => s.loadConversation)

  const upsertConversation = useHistoryStore((s) => s.upsertConversation)

  const [conversationId, setConversationId] = useState<string | null>(
    activeConversation?.id ?? null
  )

  const { send: wsSend } = useWebSocket(conversationId)
  const isFirstMessage = useRef(!activeConversation)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return

      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toISOString(),
      }

      // Read current state directly to avoid stale closure issues
      const currentConv = useConversationStore.getState().activeConversation

      if (isFirstMessage.current || !currentConv) {
        setIsTyping(true)
        setError(null)

        // Generate ID ahead of time for optimistic update
        const cid = conversationId || generateId()
        setConversationId(cid)
        startConversation(cid, userMsg, null) // Optimistic start

        try {
          const res = await supportApi.start({
            message: text.trim(),
            conversation_id: cid,
          })

          const assistantMsg: Message = {
            id: generateId(),
            role: 'assistant',
            content: res.reply,
            timestamp: new Date().toISOString(),
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
          }

          // Complete the optimistic start with assistant response
          updateMeta({
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
          })
          appendMessage(assistantMsg)
          setIsTyping(false)
          isFirstMessage.current = false

          upsertConversation({
            id: res.conversation_id,
            firstMessage: text.trim(),
            issueType: res.issue_type,
            severity: res.severity,
            status: res.status,
            messageCount: 2,
            createdAt: userMsg.timestamp,
            updatedAt: assistantMsg.timestamp,
            messages: [userMsg, assistantMsg],
          })
        } catch (err) {
          setIsTyping(false)
          setError((err as { message?: string })?.message ?? 'Failed to start conversation')
        }
      } else {
        appendMessage(userMsg)
        setIsTyping(true)
        setError(null)

        // Update local history message count optimistically
        const updatedCount = (currentConv.messages.length || 0) + 1
        upsertConversation({
          ...currentConv,
          firstMessage: currentConv.firstMessage || currentConv.messages[0]?.content || text.trim(),
          messages: [...currentConv.messages, userMsg],
          messageCount: updatedCount,
          updatedAt: userMsg.timestamp,
        })

        const currentWsStatus = useConversationStore.getState().wsStatus
        if (currentWsStatus === 'open') {
          wsSend(text.trim())
          // Note: WebSocket response handling should also call upsertConversation to keep count accurate
        } else {
          // Fallback to REST if WebSocket isn't ready
          try {
            const res = await supportApi.start({
              message: text.trim(),
              conversation_id: currentConv.id,
            })
            setIsTyping(false)
            const assistantMsg: Message = {
              id: generateId(),
              role: 'assistant',
              content: res.reply,
              timestamp: new Date().toISOString(),
              issueType: res.issue_type,
              severity: res.severity,
              status: res.status,
            }
            appendMessage(assistantMsg)
            updateMeta({
              issueType: res.issue_type,
              severity: res.severity,
              status: res.status,
            })

            // Update local history with assistant response
            const finalCount = updatedCount + 1
            upsertConversation({
              ...currentConv,
              messages: [...currentConv.messages, userMsg, assistantMsg],
              messageCount: finalCount,
              updatedAt: assistantMsg.timestamp,
              issueType: res.issue_type,
              severity: res.severity,
              status: res.status,
            })
          } catch (err) {
            setIsTyping(false)
            setError((err as { message?: string })?.message ?? 'Failed to send message')
          }
        }
      }
    },
    // Stable action refs from Zustand — these never change identity
    [
      conversationId,
      startConversation,
      appendMessage,
      updateMeta,
      setIsTyping,
      setError,
      upsertConversation,
      wsSend,
    ]
  )

  const resetConversation = useCallback(() => {
    reset()
    setConversationId(null)
    isFirstMessage.current = true
  }, [reset])

  const loadConversation = useCallback(
    async (conv: Parameters<typeof loadConversationAction>[0]) => {
      loadConversationAction(conv)
      setConversationId(conv.id)
      isFirstMessage.current = false

      // Sync with backend history if possible
      try {
        const history = await supportApi.history(conv.id)
        if (history.length > 0) {
          const mappedMessages: Message[] = history.map((h) => ({
            id: h.id,
            role: h.role as 'user' | 'assistant',
            content: h.content,
            timestamp: h.timestamp || new Date().toISOString(),
            issueType: h.issue_type,
            severity: h.severity,
            status: h.status,
          }))

          loadConversationAction({
            ...conv,
            messages: mappedMessages,
          })
        }
      } catch (err) {
        console.error('Failed to sync history:', err)
      }
    },
    [loadConversationAction]
  )

  return {
    activeConversation,
    messages: activeConversation?.messages ?? [],
    wsStatus,
    isTyping,
    error,
    sendMessage,
    resetConversation,
    loadConversation,
  }
}
