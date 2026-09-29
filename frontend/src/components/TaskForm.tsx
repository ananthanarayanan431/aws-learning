import { useState } from 'react'
import type { Category, Priority, TaskInput } from '../types'

interface Props {
  categories: Category[]
  defaultPlanned?: string
  onSubmit: (input: TaskInput) => Promise<void>
}

const PRIORITIES: Priority[] = ['low', 'medium', 'high', 'urgent']
const field = 'rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none'

export function TaskForm({ categories, defaultPlanned, onSubmit }: Props) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<Priority>('medium')
  const [categoryId, setCategoryId] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [planned, setPlanned] = useState(defaultPlanned ?? '')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setBusy(true)
    try {
      await onSubmit({
        title: title.trim(),
        priority,
        category_id: categoryId ? Number(categoryId) : null,
        due_date: dueDate || null,
        planned_date: planned || null,
      })
      setTitle('')
      setDueDate('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2 rounded-lg border border-slate-200 bg-white p-3">
      <input
        className={`${field} w-full`}
        placeholder="Add a task…"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
      />
      <div className="flex flex-wrap items-center gap-2">
        <select className={field} value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
          {PRIORITIES.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
        <select className={field} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">No category</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1 text-xs text-slate-500">
          Plan
          <input type="date" className={field} value={planned} onChange={(e) => setPlanned(e.target.value)} />
        </label>
        <label className="flex items-center gap-1 text-xs text-slate-500">
          Due
          <input type="date" className={field} value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </label>
        <button
          disabled={busy || !title.trim()}
          className="ml-auto rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Add
        </button>
      </div>
    </form>
  )
}
