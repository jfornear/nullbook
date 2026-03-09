import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type { Conversation, ConversationDetail, SendMessageResponse } from "@/types/chat";

export function useConversations() {
  return useQuery<Conversation[]>({
    queryKey: ["conversations"],
    queryFn: async () => {
      const res = await api.get<{ results: Conversation[] }>("/chat/conversations/");
      return res.results;
    },
  });
}

export function useConversation(id: string | undefined) {
  return useQuery<ConversationDetail>({
    queryKey: ["conversation", id],
    queryFn: () => api.get<ConversationDetail>(`/chat/conversations/${id}/`),
    enabled: !!id,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { title?: string }) => api.post<Conversation>("/chat/conversations/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, content }: { conversationId: string; content: string }) =>
      api.post<SendMessageResponse>(`/chat/conversations/${conversationId}/send/`, { content }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["conversation", variables.conversationId],
      });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/chat/conversations/${id}/`),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: ["conversation", id] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function usePinConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_pinned }: { id: string; is_pinned: boolean }) =>
      api.patch<Conversation>(`/chat/conversations/${id}/`, { is_pinned }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useArchiveConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.patch<Conversation>(`/chat/conversations/${id}/`, { is_archived: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
