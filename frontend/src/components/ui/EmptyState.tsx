import type { ReactNode } from "react"

type EmptyStateProps = {
  title: string
  body: string
  action?: ReactNode
}

export function EmptyState({ title, body, action }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-line px-5 py-10 text-center">
      <h2 className="font-display text-xl font-medium">{title}</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm text-muted">{body}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
