type TabsProps = {
  label: string
  value: string
  onChange: (value: string) => void
  tabs: Array<{ id: string; label: string }>
}

export function Tabs({ label, value, onChange, tabs }: TabsProps) {
  return (
    <div role="tablist" aria-label={label} className="flex gap-2 overflow-x-auto">
      {tabs.map((tab) => {
        const selected = tab.id === value
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={selected}
            aria-controls={`panel-${tab.id}`}
            className={selected
              ? "rounded-full bg-ink px-4 py-2 text-sm font-semibold text-card focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              : "rounded-full border border-line bg-card px-4 py-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
