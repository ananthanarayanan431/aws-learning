import { useState } from 'react'
import { errorMessage } from '../hooks'
import type { Category, Priority, TaskInput } from '../types'

interface Props {
  categories: Category[]
  onCreateCategory: (name: string) => Promise<Category>
  defaultPlanned?: string
  onSubmit: (input: TaskInput) => Promise<void>
}

const PRIORITIES: Priority[] = ['low', 'medium', 'high', 'urgent']
const field = 'rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none'

const NEW_CATEGORY = '__new__'

export function TaskForm({ categories, onCreateCategory, defaultPlanned, onSubmit }: Props) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<Priority>('medium')
  const [categoryId, setCategoryId] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [planned, setPlanned] = useState(defaultPlanned ?? '')
  const [busy, setBusy] = useState(false)
  const [newCategory, setNewCategory] = useState<string | null>(null) // non-null while creating
  const [categoryError, setCategoryError] = useState<string | null>(null)

  // A category deleted elsewhere must not stay selected.
  const selectedCategory = categories.some((c) => String(c.id) === categoryId) ? categoryId : ''

  async function createCategory() {
    const name = (newCategory ?? '').trim()
    if (!name) return
    try {
      const created = await onCreateCategory(name)
      setCategoryId(String(created.id))
      setNewCategory(null)
      setCategoryError(null)
    } catch (e) {
      setCategoryError(errorMessage(e))
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setBusy(true)
    try {
      await onSubmit({
        title: title.trim(),
        priority,
        category_id: selectedCategory ? Number(selectedCategory) : null,
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
        {newCategory === null ? (
          <select
            className={field}
            value={selectedCategory}
            onChange={(e) => {
              if (e.target.value === NEW_CATEGORY) setNewCategory('')
              else setCategoryId(e.target.value)
            }}
          >
            <option value="">No category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
            <option value={NEW_CATEGORY}>+ New category…</option>
          </select>
        ) : (
          <span className="flex items-center gap-1">
            <input
              autoFocus
              className={`${field} w-36`}
              placeholder="Category name"
              value={newCategory}
              maxLength={100}
              onChange={(e) => setNewCategory(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  createCategory()
                } else if (e.key === 'Escape') {
                  setNewCategory(null)
                  setCategoryError(null)
                }
              }}
            />
            <button
              type="button"
              disabled={!newCategory.trim()}
              onClick={createCategory}
              className="rounded-md bg-slate-800 px-2 py-1.5 text-xs font-medium text-white hover:bg-slate-900 disabled:opacity-50"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => {
                setNewCategory(null)
                setCategoryError(null)
              }}
              className="px-1 text-xs text-slate-500 hover:text-slate-700"
            >
              Cancel
            </button>
          </span>
        )}
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
      {categoryError && <p className="text-xs text-red-600">{categoryError}</p>}
    </form>
  )
}
