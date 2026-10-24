import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { createApiToken, deleteApiToken, listApiTokens } from "../api/apiTokens.ts"
import { ApiError } from "../api/client.ts"
import type { NewApiToken } from "../types/api.ts"
import { Button } from "./ui/Button.tsx"
import { Card } from "./ui/Card.tsx"
import { useToast } from "./ui/Toast.tsx"

function browserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
  } catch {
    return "UTC"
  }
}

export function SiriCard() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const tokens = useQuery({ queryKey: ["api-tokens"], queryFn: listApiTokens })
  const [created, setCreated] = useState<NewApiToken | null>(null)
  const [busy, setBusy] = useState(false)
  const endpoint = `${window.location.origin}/api/v1/voice-log`

  async function create() {
    setBusy(true)
    try {
      setCreated(await createApiToken("iPhone Shortcut", browserTimeZone()))
      await queryClient.invalidateQueries({ queryKey: ["api-tokens"] })
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "The Siri key could not be created.", "danger")
    } finally {
      setBusy(false)
    }
  }

  async function remove(id: number) {
    try {
      await deleteApiToken(id)
      if (created?.id === id) setCreated(null)
      await queryClient.invalidateQueries({ queryKey: ["api-tokens"] })
      toast.push("Siri key deleted. Shortcuts using it will stop working.")
    } catch (error) {
      toast.push(error instanceof ApiError ? error.message : "The key could not be deleted.", "danger")
    }
  }

  return (
    <Card>
      <h2 className="font-display text-xl font-medium">Log food with Siri</h2>
      <p className="mt-2 text-sm text-muted">
        Say “Hey Siri, log food”, then what you ate, like “two eggs and a slice of toast for breakfast”.
        Siri reads back what was logged and the calories you have left today. Foods are matched to USDA
        entries and servings, and you can check or remove them in your diary.
      </p>

      {created ? (
        <div className="mt-4 space-y-3 rounded-2xl border border-accent bg-accent-soft p-4">
          <p className="text-sm font-semibold">Your Siri key. Copy it now: it won't be shown again.</p>
          <CopyField label="Authorization header value" value={`Bearer ${created.key}`} />
        </div>
      ) : null}

      <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm">
        <li>{created ? "Done: your key is above." : "Create a Siri key below and copy it."}</li>
        <li>On your iPhone, open the <b>Shortcuts</b> app, tap <b>+</b>, and name the shortcut <b>Log food</b>.</li>
        <li>Add the action <b>Dictate Text</b>.</li>
        <li>
          Add <b>Get Contents of URL</b>. Set the URL to the address below, tap <b>Show More</b>, and choose:
          Method <b>POST</b>; a header named <b>Authorization</b> with your key as the value; Request Body <b>JSON</b>
          with a text field named <b>text</b> set to <b>Dictated Text</b>.
        </li>
        <li>Add <b>Get Dictionary Value</b>, with Key <b>spoken</b>.</li>
        <li>Add <b>Speak Text</b> and pick <b>Dictionary Value</b>.</li>
        <li>Say <b>“Hey Siri, log food”</b>. Siri uses the shortcut's name, so you can rename it.</li>
      </ol>
      <div className="mt-3">
        <CopyField label="Shortcut URL" value={endpoint} />
      </div>
      <p className="mt-3 text-sm text-muted">
        The meal comes from what you say (“for lunch”), or else the time of day. Amounts can be counts
        (“two eggs”), sizes (“a large banana”), servings (“a cup of rice”, “a slice of toast”) or weights
        (“200 grams of chicken”).
      </p>

      <div className="mt-4 border-t border-line pt-4">
        {tokens.data && tokens.data.tokens.length > 0 ? (
          <ul className="mb-3 space-y-2">
            {tokens.data.tokens.map((token) => (
              <li key={token.id} className="flex items-center justify-between gap-3 text-sm">
                <span>
                  <span className="block font-semibold">{token.name}</span>
                  <span className="text-muted">
                    {token.last_used_at ? `Last used ${new Date(token.last_used_at).toLocaleString()}` : "Not used yet"}
                  </span>
                </span>
                <Button variant="ghost" size="sm" onClick={() => void remove(token.id)}>Delete</Button>
              </li>
            ))}
          </ul>
        ) : null}
        <Button variant="secondary" disabled={busy} onClick={() => void create()}>
          {busy ? "Creating…" : "Create a Siri key"}
        </Button>
      </div>
    </Card>
  )
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <div className="mt-1 flex items-stretch gap-2">
        <code className="min-w-0 flex-1 overflow-x-auto whitespace-nowrap rounded-xl border border-line bg-card px-3 py-2.5 text-sm select-all">{value}</code>
        <Button
          variant="secondary"
          size="sm"
          className="shrink-0"
          onClick={() => {
            void navigator.clipboard?.writeText(value).then(() => {
              setCopied(true)
              window.setTimeout(() => setCopied(false), 1600)
            }).catch(() => setCopied(false))
          }}
        >
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </div>
  )
}
