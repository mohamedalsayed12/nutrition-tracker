import { useEffect, useId, useRef, type ReactNode } from "react"
import { cn } from "../../lib/cn.ts"

type OverlayProps = {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  sheet?: boolean
}

export function Modal(props: Omit<OverlayProps, "sheet">) {
  return <Overlay {...props} />
}

export function Sheet(props: Omit<OverlayProps, "sheet">) {
  return <Overlay {...props} sheet />
}

function Overlay({ open, title, onClose, children, sheet = false }: OverlayProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      className={cn(sheet && "sheet")}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose()
      }}
    >
      <div className={cn("w-[min(100vw-2rem,28rem)] rounded-3xl border border-line bg-card p-5 text-ink shadow-xl", sheet && "w-screen rounded-b-none")}>
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={titleId} className="font-display text-xl font-medium">{title}</h2>
          <button
            type="button"
            className="rounded-full px-3 py-1 text-sm font-semibold text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            onClick={onClose}
          >
            Close
          </button>
        </div>
        {children}
      </div>
    </dialog>
  )
}
