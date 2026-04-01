import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/useToast'
import { useHistoryStore } from '@/store/historyStore'
import { useConversationStore } from '@/store/conversationStore'
import { supportApi } from '@/lib/api'
import type { StoredConversation } from '@/types/conversation'
import { truncate } from '@/lib/utils'
import { IssueTypeBadge } from './IssueTypeBadge'
import { SeverityBadge } from './SeverityBadge'
import { StatusChip } from './StatusChip'

interface Props {
  conversation: StoredConversation
  children: React.ReactNode
}

export function DeleteConversationDialog({ conversation, children }: Props) {
  const [open, setOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const { toast } = useToast()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDeleting(true)
    try {
      await supportApi.deleteHistory(conversation.id)

      useHistoryStore.getState().deleteConversation(conversation.id)

      if (useConversationStore.getState().activeConversation?.id === conversation.id) {
        useConversationStore.getState().reset()
      }

      toast({
        title: 'Conversation deleted',
        description: 'The chat history has been permanently removed.',
      })
      setOpen(false)
    } catch (error) {
      toast({
        title: 'Failed to delete',
        description: 'An error occurred while deleting the conversation.',
        variant: 'destructive',
      })
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        {children}
      </AlertDialogTrigger>
      <AlertDialogContent onClick={(e) => e.stopPropagation()}>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to permanently delete this chat history? This action cannot be undone.
          </AlertDialogDescription>
          
          <div className="bg-muted/50 p-3 rounded-md flex flex-col gap-2 my-2 border">
            <p className="text-sm font-medium text-foreground line-clamp-2">
              {truncate(conversation.firstMessage || (conversation.messages && conversation.messages[0]?.content) || 'Empty conversation', 120)}
            </p>
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              <IssueTypeBadge issueType={conversation.issueType} />
              <SeverityBadge severity={conversation.severity} />
              <StatusChip status={conversation.status} />
            </div>
          </div>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive hover:bg-destructive/90 text-destructive-foreground focus:ring-destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Yes, delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
