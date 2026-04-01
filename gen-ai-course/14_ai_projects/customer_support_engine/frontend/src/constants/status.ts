import type { SupportStatus } from '@/types/api'
import type { IssueType } from '@/types/api'

export const STATUS_CONFIG: Record<SupportStatus, { label: string; className: string }> = {
  open: {
    label: 'Open',
    className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  },
  resolving: {
    label: 'Resolving',
    className: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  },
  resolved: {
    label: 'Resolved',
    className: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  },
  escalated: {
    label: 'Escalated',
    className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  },
}

export const ISSUE_TYPE_CONFIG: Record<IssueType, { label: string; className: string }> = {
  billing: {
    label: 'Billing',
    className: 'bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-400',
  },
  technical: {
    label: 'Technical',
    className: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400',
  },
  general: {
    label: 'General',
    className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  },
  greeting: {
    label: 'Greeting',
    className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  },
}
