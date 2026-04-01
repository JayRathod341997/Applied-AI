// Exact mirrors of the backend state.py literals
export type IssueType = 'billing' | 'technical' | 'general' | 'greeting'
export type Severity = 'low' | 'medium' | 'high' | 'critical'
export type SupportStatus = 'open' | 'resolving' | 'resolved' | 'escalated'

export interface StartRequest {
  message: string
  conversation_id?: string
}

export interface StartResponse {
  conversation_id: string
  reply: string
  issue_type: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
}

export interface WsInboundMessage {
  reply: string
  issue_type: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
}

export interface WsErrorMessage {
  error: string
}

export type WsServerMessage = WsInboundMessage | WsErrorMessage

export function isWsError(msg: WsServerMessage): msg is WsErrorMessage {
  return 'error' in msg
}

export interface HealthResponse {
  status: 'ok'
  service: string
}

export interface HistoryItem {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  issue_type?: IssueType | null
  severity?: Severity | null
  status?: SupportStatus | null
}
