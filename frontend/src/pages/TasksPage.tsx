import { useCallback, useState } from 'react'
import { api } from '../api'
import { TaskForm } from '../components/TaskForm'
import { TaskList } from '../components/TaskList'
import { CategoryManager } from '../components/CategoryManager'
import { useTasks } from '../hooks'
import { useCategories } from '../store/categories'
import type { Category } from '../types'

const sel = 'rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm'

export function TasksPage() {
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [search, setSearch] = useState('')
  const { categories, addCategory, removeCategory } = useCategories()

  const load = useCallback(() => {
    const params: Record<string, string> = {}
    if (status) params.status = status
    if (priority) params.priority = priority
    if (categoryId) params.category_id = categoryId
    if (search.trim()) params.search = search.trim()
    return api.listTasks(params)
  }, [status, priority, categoryId, search])

  const { tasks, loading, error, reload, create, toggle, remove, addSubtask } = useTasks(load)

  async function deleteCategory(c: Category) {
    await removeCategory(c.id)
    if (categoryId === String(c.id)) setCategoryId('')
    await reload() // tasks that had this category now have none
  }

  return (
    <div className="space-y-4">
      <TaskForm categories={categories} onCreateCategory={addCategory} onSubmit={create} />
      <div className="flex flex-wrap gap-2">
        <input className={sel} placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className={sel} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Any status</option>
          <option value="todo">To do</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
        </select>
        <select className={sel} value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="">Any priority</option>
          {['low', 'medium', 'high', 'urgent'].map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
        <select className={sel} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">Any category</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <CategoryManager categories={categories} onDelete={deleteCategory} />
      {error && <p className="rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <TaskList tasks={tasks} empty="No tasks match." onToggle={toggle} onDelete={remove} onAddSubtask={addSubtask} />
      )}
    </div>
  )
}
