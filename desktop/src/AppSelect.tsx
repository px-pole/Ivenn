import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

type Option = {
  value: string
  label: string
}

type Props = {
  ariaLabel: string
  value: string
  options: Option[]
  onChange: (value: string) => void
  leadingIcon?: ReactNode
}

export function AppSelect({ ariaLabel, value, options, onChange, leadingIcon }: Props) {
  const [open, setOpen] = useState(false)
  const container = useRef<HTMLDivElement>(null)
  const listboxId = useId()
  const selected = options.find((option) => option.value === value) ?? options[0]

  useEffect(() => {
    function closeWhenFocusLeaves(event: PointerEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false)
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('pointerdown', closeWhenFocusLeaves)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('pointerdown', closeWhenFocusLeaves)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [])

  if (!selected) return null

  return (
    <div className="app-select" ref={container}>
      <button className="app-select-trigger" type="button" aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} aria-controls={listboxId} onClick={() => setOpen((isOpen) => !isOpen)}>
        {leadingIcon && <span className="app-select-icon" aria-hidden="true">{leadingIcon}</span>}<span className="app-select-label">{selected.label}</span><ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && (
        <div className="app-select-menu" id={listboxId} role="listbox" aria-label={ariaLabel}>
          {options.map((option) => <button className={option.value === value ? 'selected' : ''} type="button" role="option" aria-selected={option.value === value} key={option.value} onClick={() => { onChange(option.value); setOpen(false) }}>{option.label}</button>)}
        </div>
      )}
    </div>
  )
}