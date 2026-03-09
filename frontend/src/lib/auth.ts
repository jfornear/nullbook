import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, setCsrfToken } from "./api";

interface User {
  id: number;
  username: string;
  email: string;
}

export function useSession() {
  return useQuery<User>({
    queryKey: ["session"],
    queryFn: () => api.get<User>("/auth/session/"),
    retry: false,
    staleTime: Infinity,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      api.post<User & { csrfToken: string }>("/auth/login/", credentials),
    onSuccess: (data) => {
      setCsrfToken(data.csrfToken);
      queryClient.invalidateQueries({ queryKey: ["session"] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/auth/logout/"),
    onSuccess: () => {
      // Reset session query to trigger re-fetch (will fail → shows login)
      queryClient.resetQueries({ queryKey: ["session"] });
      // Clear all other cached data
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== "session" });
    },
  });
}

export async function initCsrf() {
  const res = await api.get<{ csrfToken: string }>("/auth/csrf/");
  setCsrfToken(res.csrfToken);
}
