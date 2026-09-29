import { useCallback, useMemo, useState } from 'react'
import { api } from '../api'
import { TaskForm } from '../components/TaskForm'
import { TaskList } from '../components/TaskList'
import { monthGrid, toISO, todayISO } from '../date'
import { useTasks } from '../hooks'
import { useCategories } from '../store/categories'
import type { Priority, Task } from '../types'

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MAX_CHIPS = 3

const chipStyle: Record<Priority, string> = {
  low: 'border-slate-300 bg-slate-50 text-slate-600',
  medium: 'border-sky-300 bg-sky-50 text-sky-800',
  high: 'border-amber-400 bg-amber-50 text-amber-800',
  urgent: 'border-rose-400 bg-rose-50 text-rose-800',
}

/** The day a task appears on: its planned date, else its due date. */
const shownOn = (t: Task) => t.planned_date ?? t.due_date

export function CalendarPage() {
  const today = todayISO()
  const [cursor, setCursor] = useState(() => {
    const n = new Date()
    return { year: n.getFullYear(), month: n.getMonth() }
  })
  const [selected, setSelected] = useState(today)
  const { categories, addCategory } = useCategories()

  const days = useMemo(() => monthGrid(cursor.year, cursor.month), [cursor])
  const from = toISO(days[0])
  const to = toISO(days[days.length - 1])

  const load = useCallback(() => api.listTasks({ date_from: from, date_to: to, limit: '500' }), [from, to])
  const { tasks, loading, error, create, toggle, remove, addSubtask } = useTasks(load)

  const byDay = useMemo(() => {
    const map = new Map<string, Task[]>()
    for (const t of tasks) {
      const day = shownOn(t)
      if (day) map.set(day, [...(map.get(day) ?? []), t])
    }
    return map
  }, [tasks])

  function shift(delta: number) {
    setCursor(({ year, month }) => {
      const d = new Date(year, month + delta, 1)
      return { year: d.getFullYear(), month: d.getMonth() }
    })
  }

  function goToday() {
    const n = new Date()
    setCursor({ year: n.getFullYear(), month: n.getMonth() })
    setSelected(today)
  }

  const title = new Date(cursor.year, cursor.month, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })
  const selectedTasks = byDay.get(selected) ?? []
  const selectedLabel = new Date(selected + 'T00:00').toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  const navBtn = 'rounded-md border border-slate-300 bg-white px-2.5 py-1 text-sm hover:bg-slate-100'

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        <div className="flex gap-1">
          <button aria-label="Previous month" className={navBtn} onClick={() => shift(-1)}>
            ‹
          </button>
          <button className={navBtn} onClick={goToday}>
            Today
          </button>
          <button aria-label="Next month" className={navBtn} onClick={() => shift(1)}>
            ›
          </button>
        </div>
      </div>

      {error && <p className="rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50 text-center text-xs font-medium text-slate-500">
          {WEEKDAYS.map((d) => (
            <div key={d} className="py-1.5">
              {d}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7">
          {days.map((d) => {
            const iso = toISO(d)
            const inMonth = d.getMonth() === cursor.month
            const dayTasks = byDay.get(iso) ?? []
            const isSelected = iso === selected
            return (
              <button
                key={iso}
                type="button"
                onClick={() => setSelected(iso)}
                className={`flex min-h-24 flex-col gap-0.5 border-b border-r border-slate-100 p-1 text-left align-top hover:bg-indigo-50/40 ${
                  inMonth ? '' : 'bg-slate-50/70 text-slate-400'
                } ${isSelected ? 'ring-2 ring-inset ring-indigo-500' : ''}`}
              >
                <span
                  className={`ml-auto flex h-5 w-5 items-center justify-center rounded-full text-xs ${
                    iso === today ? 'bg-indigo-600 font-semibold text-white' : ''
                  }`}
                >
                  {d.getDate()}
                </span>
                {dayTasks.slice(0, MAX_CHIPS).map((t) => (
                  <span
                    key={t.id}
                    title={t.title}
                    className={`truncate rounded border-l-2 px-1 text-[11px] leading-4 ${chipStyle[t.priority]} ${
                      t.status === 'done' ? 'line-through opacity-60' : ''
                    }`}
                  >
                    {t.title}
                  </span>
                ))}
                {dayTasks.length > MAX_CHIPS && (
                  <span className="px-1 text-[11px] text-slate-500">+{dayTasks.length - MAX_CHIPS} more</span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-slate-600">{selectedLabel}</h3>
        <TaskForm
          key={selected}
          categories={categories}
          onCreateCategory={addCategory}
          defaultPlanned={selected}
          onSubmit={create}
        />
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <TaskList
            tasks={selectedTasks}
            empty="Nothing on this day."
            onToggle={toggle}
            onDelete={remove}
            onAddSubtask={addSubtask}
          />
        )}
      </section>
    </div>
  )
}
