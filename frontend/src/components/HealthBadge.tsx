import { useEffect, useState } from 'react'
import { api } from '../api'

type State = 'checking' | 'ok' | 'down'

function useCheck(fn: () => Promise<unknown>): State {
  const [state, setState] = useState<State>('checking')
  useEffect(() => {
    let alive = true
    const run = () =>
      fn().then(
        () => alive && setState('ok'),
        () => alive && setState('down'),
      )
    run()
    const id = setInterval(run, 30_000)
    return () => {
      alive = false
      clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return state
}

const colors: Record<State, string> = {
  checking: 'bg-slate-300',
  ok: 'bg-emerald-500',
  down: 'bg-rose-500',
}

function Dot({ label, state }: { label: string; state: State }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-slate-500" title={`${label}: ${state}`}>
      <span className={`h-2 w-2 rounded-full ${colors[state]}`} />
      {label}
    </span>
  )
}

export function HealthBadge() {
  const backend = useCheck(api.health)
  const db = useCheck(api.healthDb)
  return (
    <div className="flex gap-3">
      <Dot label="API" state={backend} />
      <Dot label="DB" state={db} />
    </div>
  )
}
