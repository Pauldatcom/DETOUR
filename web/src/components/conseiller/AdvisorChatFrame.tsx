import type { FormEvent, ReactNode, RefObject } from "react";
import { BrandLogo } from "./BrandLogo";

/**
 * Branded chrome for the advisor / traveler chatbot surface.
 * One yellow accent only: the monogram O (send button stays ink).
 */

interface AdvisorChatFrameProps {
  title: string;
  subtitle?: string;
  open: boolean;
  onClose: () => void;
  onToggle: () => void;
  scrollRef: RefObject<HTMLDivElement | null>;
  children: ReactNode;
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  loading?: boolean;
  inputPlaceholder?: string;
  submitDisabled?: boolean;
  error?: string;
  launcherLabelOpen?: string;
  launcherLabelClosed?: string;
}

export function AdvisorChatFrame({
  title,
  subtitle,
  open,
  onClose,
  onToggle,
  scrollRef,
  children,
  input,
  onInputChange,
  onSubmit,
  loading = false,
  inputPlaceholder = "Votre message…",
  submitDisabled = false,
  error = "",
  launcherLabelOpen = "Fermer le chat",
  launcherLabelClosed = "Ouvrir le chat",
}: AdvisorChatFrameProps) {
  return (
    <>
      <button
        type="button"
        onClick={onToggle}
        className="fixed bottom-6 left-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-ink text-chalk shadow-lg transition outline-none hover:bg-ink/90 focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-yellow"
        aria-label={open ? launcherLabelOpen : launcherLabelClosed}
        aria-expanded={open}
      >
        {open ? (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        ) : (
          <BrandLogo width={36} variant="monogram" alt="" className="pointer-events-none" />
        )}
      </button>

      {open && (
        <div
          className="fixed bottom-24 left-6 z-40 flex h-[420px] max-h-[80vh] w-[360px] max-w-[calc(100vw-3rem)] flex-col overflow-hidden rounded-2xl border border-ink/10 bg-chalk shadow-2xl"
          role="dialog"
          aria-label={title}
        >
          <div className="flex items-center justify-between bg-ink px-4 py-3 text-chalk">
            <div className="flex min-w-0 items-center gap-3">
              <BrandLogo width={40} variant="monogram" alt="" />
              <div className="min-w-0">
                <p className="truncate font-display text-sm font-semibold tracking-tight">
                  {title}
                </p>
                {subtitle && <p className="truncate text-[10px] text-sky">{subtitle}</p>}
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1 text-chalk/70 outline-none hover:bg-chalk/10 hover:text-chalk"
              aria-label="Fermer"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-card px-4 py-3">
            {children}
            {error && (
              <p role="alert" className="text-xs text-brick">
                {error}
              </p>
            )}
          </div>

          <form
            onSubmit={onSubmit}
            className="flex items-center gap-2 border-t border-ink/10 bg-chalk px-3 py-2.5"
          >
            <input
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              placeholder={inputPlaceholder}
              disabled={loading}
              className="flex-1 rounded-full bg-white px-4 py-2 text-sm text-ink outline-none placeholder:text-ballast focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-1 focus-visible:outline-yellow"
            />
            <button
              type="submit"
              disabled={loading || submitDisabled}
              className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-ink text-chalk transition outline-none hover:bg-ink/90 disabled:opacity-50"
              aria-label="Envoyer"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3 3l18 9-18 9 3-9Z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
