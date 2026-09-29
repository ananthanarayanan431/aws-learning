import { useState } from 'react'
import type { Priority, Task } from '../types'

interface Props {
  task: Task
  onToggle: (task: Task) => void
  onDelete: (task: Task) => void
  onAddSubtask: (parent: Task, title: string) => Promise<void>
  today: string
}

const priorityStyle: Record<Priority, string> = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-sky-100 text-sky-700',
  high: 'bg-amber-100 text-amber-700',
  urgent: 'bg-rose-100 text-rose-700',
}

export function TaskItem({ task, onToggle, onDelete, onAddSubtask, today }: Props) {
  const [adding, setAdding] = useState(false)
  const [sub, setSub] = useState('')
  const done = task.status === 'done'
  const overdue = !done && task.due_date !== null && task.due_date < today

  async function addSub(e: React.FormEvent) {
    e.preventDefault()
    if (!sub.trim()) return
    await onAddSubtask(task, sub.trim())
    setSub('')
    setAdding(false)
  }

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex items-start gap-3">
        <input type="checkbox" className="mt-1 h-4 w-4" checked={done} onChange={() => onToggle(task)} />
        <div className="min-w-0 flex-1">
          <p className={done ? 'text-slate-400 line-through' : 'text-slate-900'}>{task.title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
            <span className={`rounded px-1.5 py-0.5 ${priorityStyle[task.priority]}`}>{task.priority}</span>
            {task.category && (
              <span className="rounded px-1.5 py-0.5 text-white" style={{ backgroundColor: task.category.color }}>
                {task.category.name}
              </span>
            )}
            {task.tags.map((t) => (
              <span key={t.id} className="text-slate-500">
                #{t.name}
              </span>
            ))}
            {task.due_date && (
              <span className={overdue ? 'font-medium text-rose-600' : 'text-slate-500'}>Due {task.due_date}</span>
            )}
          </div>
        </div>
        <button onClick={() => setAdding((a) => !a)} className="text-xs text-slate-400 hover:text-indigo-600">
          + subtask
        </button>
        <button onClick={() => onDelete(task)} className="text-xs text-slate-400 hover:text-rose-600">
          Delete
        </button>
      </div>

      {(task.subtasks.length > 0 || adding) && (
        <ul className="mt-2 ml-7 space-y-1">
          {task.subtasks.map((s) => (
            <li key={s.id} className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={s.status === 'done'} onChange={() => onToggle(s)} />
              <span className={s.status === 'done' ? 'flex-1 text-slate-400 line-through' : 'flex-1'}>{s.title}</span>
              <button onClick={() => onDelete(s)} className="text-xs text-slate-400 hover:text-rose-600">
                ✕
              </button>
            </li>
          ))}
          {adding && (
            <form onSubmit={addSub}>
              <input
                autoFocus
                className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
                placeholder="Subtask title, then Enter"
                value={sub}
                onChange={(e) => setSub(e.target.value)}
              />
            </form>
          )}
        </ul>
      )}
    </li>
  )
}
