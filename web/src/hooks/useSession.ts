import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import type { Session } from "../types";

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (): Promise<Session> => {
    try {
      return await api.session();
    } catch {
      return { connecte: false };
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    const s = await load();
    setSession(s);
    setLoading(false);
  }, [load]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const s = await load();
      if (cancelled) return;
      setSession(s);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  return { session, loading, refresh, setSession };
}
