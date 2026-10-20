import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import type { Session } from "../types";

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const s = await api.session();
      setSession(s);
    } catch {
      setSession({ connecte: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { session, loading, refresh, setSession };
}