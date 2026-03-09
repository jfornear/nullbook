import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Archive, MoreHorizontal, Pin, Trash2 } from "lucide-react";
import { useDeleteConversation, usePinConversation, useArchiveConversation } from "@/lib/chat";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

interface ConversationActionsProps {
  id: string;
  title: string;
  isPinned: boolean;
  triggerClassName?: string;
}

export function ConversationActions({
  id,
  title,
  isPinned,
  triggerClassName,
}: ConversationActionsProps) {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const deleteMutation = useDeleteConversation();
  const pinMutation = usePinConversation();
  const archiveMutation = useArchiveConversation();
  const [showDelete, setShowDelete] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className={triggerClassName ?? "h-6 w-6"}
            aria-label={`Actions for ${title}`}
            onClick={(e) => e.stopPropagation()}
          >
            <MoreHorizontal className="h-3.5 w-3.5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
          <DropdownMenuItem onClick={() => pinMutation.mutate({ id, is_pinned: !isPinned })}>
            <Pin className="mr-2 h-4 w-4" />
            {isPinned ? "Unpin" : "Pin"}
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => {
              archiveMutation.mutate(id);
              if (conversationId === id) navigate("/");
            }}
          >
            <Archive className="mr-2 h-4 w-4" />
            Archive
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-red-500 focus:text-red-500"
            onClick={() => setShowDelete(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ConfirmDialog
        open={showDelete}
        onOpenChange={(open) => !open && setShowDelete(false)}
        title="Delete Conversation"
        description={`Delete "${title}"? This cannot be undone.`}
        onConfirm={() => {
          deleteMutation.mutate(id, {
            onSuccess: () => {
              if (conversationId === id) navigate("/");
              setShowDelete(false);
            },
          });
        }}
        destructive
        loading={deleteMutation.isPending}
      />
    </>
  );
}
