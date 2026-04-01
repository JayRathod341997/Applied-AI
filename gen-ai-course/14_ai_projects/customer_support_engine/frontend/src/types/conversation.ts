import type { IssueType, Severity, SupportStatus } from './api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string // ISO
  issueType?: IssueType | null
  severity?: Severity | null
  status?: SupportStatus | null
  isError?: boolean
}

export interface Conversation {
  id: string
  firstMessage: string
  messages: Message[]
  issueType: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
  messageCount: number
  createdAt: string
  updatedAt: string
}

export interface StoredConversation extends Conversation {}

export type WsStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed' | 'error'
