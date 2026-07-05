"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { POLLING_INTERVAL_MS } from "@/lib/constants";
import type { ProgressResponse } from "@/lib/types";

interface PollingResult {
  progress: ProgressResponse | null;
  error: string | null;
  done: boolean;
}

const MISSING_ID_ERROR = "잘못된 요청입니다. question_id가 없습니다.";

export function useAnalysisPolling(questionId: string | null): PollingResult {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const doneRef = useRef(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!questionId) return;

    let cancelled = false;
    doneRef.current = false;

    async function poll() {
      if (cancelled || doneRef.current || !questionId) return;
      try {
        const res = await api.progress(questionId);
        if (cancelled) return;
        setProgress(res);
        setError(null);
        if (res.status === "completed" || res.status === "failed") {
          doneRef.current = true;
          setDone(true);
          if (res.status === "failed") {
            setError(res.error_message ?? "검증 작업이 실패했습니다.");
          }
          return;
        }
        setTimeout(poll, POLLING_INTERVAL_MS);
      } catch (err) {
        if (cancelled) return;
        doneRef.current = true;
        setDone(true);
        setError(err instanceof ApiError ? err.message : "진행 상태를 불러오지 못했습니다.");
      }
    }

    poll();

    return () => {
      cancelled = true;
      doneRef.current = true;
    };
  }, [questionId]);

  if (!questionId) {
    return { progress: null, error: MISSING_ID_ERROR, done: true };
  }

  return { progress, error, done };
}
