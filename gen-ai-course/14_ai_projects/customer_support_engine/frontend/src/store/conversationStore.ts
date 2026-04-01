import { create } from 'zustand'
import type { Conversation, Message, WsStatus } from '@/types/conversation'
import type { IssueType, Severity, SupportStatus } from '@/types/api'

interface ConversationMeta {
  issueType: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
}

interface ConversationState {
  activeConversation: Conversation | null
  wsStatus: WsStatus
  isTyping: boolean
  error: string | null

  startConversation: (id: string, userMsg: Message, assistantMsg?: Message | null, meta?: Partial<ConversationMeta>) => void
  appendMessage: (message: Message) => void
  updateMeta: (meta: Partial<ConversationMeta>) => void
  setWsStatus: (status: WsStatus) => void
  setIsTyping: (v: boolean) => void
  setError: (err: string | null) => void
  reset: () => void
  loadConversation: (conversation: Conversation) => void
}

export const useConversationStore = create<ConversationState>()((set) => ({
  activeConversation: null,
  wsStatus: 'idle',
  isTyping: false,
  error: null,

  startConversation: (id, userMsg, assistantMsg, meta) =>
    set({
      activeConversation: {
        id,
        firstMessage: userMsg.content,
        messages: assistantMsg ? [userMsg, assistantMsg] : [userMsg],
        issueType: meta?.issueType ?? null,
        severity: meta?.severity ?? null,
        status: meta?.status ?? 'open',
        messageCount: assistantMsg ? 2 : 1,
        createdAt: userMsg.timestamp,
        updatedAt: assistantMsg?.timestamp ?? userMsg.timestamp,
      },
      isTyping: assistantMsg ? false : true,
      error: null,
    }),

  appendMessage: (message) =>
    set((s) => {
      if (!s.activeConversation) return {}
      return {
        activeConversation: {
          ...s.activeConversation,
          messages: [...s.activeConversation.messages, message],
          updatedAt: message.timestamp,
        },
      }
    }),

  updateMeta: (meta) =>
    set((s) => {
      if (!s.activeConversation) return {}
      return { activeConversation: { ...s.activeConversation, ...meta } }
    }),

  setWsStatus: (wsStatus) => set({ wsStatus }),
  setIsTyping: (isTyping) => set({ isTyping }),
  setError: (error) => set({ error }),
  reset: () => set({ activeConversation: null, wsStatus: 'idle', isTyping: false, error: null }),
  loadConversation: (conversation) => set({ activeConversation: conversation, wsStatus: 'idle', isTyping: false, error: null }),
}))
