import { todayISO } from '../date'
import { useState } from 'react'
import { api } from '../api'
import { TaskForm } from '../components/TaskForm'
import { TaskList } from '../components/TaskList'
import { errorMessage, useTasks } from '../hooks'
import { useCategories } from '../store/categories'

export function TodayPage() {
  const today = todayISO()
  const { tasks, loading, error, reload, create, toggle, remove, addSubtask } = useTasks(api.today)
  const { categories, addCategory } = useCategories()
  const [notice, setNotice] = useState<string | null>(null)
  const overdue = tasks.filter((t) => t.planned_date !== null && t.planned_date < today && t.status !== 'done')

  async function carryOver() {
    try {
      const { moved } = await api.carryOver()
      setNotice(`Moved ${moved} task(s) to today`)
      await reload()
    } catch (e) {
      setNotice(errorMessage(e))
    }
  }

  return (
    <div className="space-y-4">
      <TaskForm categories={categories} onCreateCategory={addCategory} defaultPlanned={today} onSubmit={create} />
      {error && <p className="rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      {overdue.length > 0 && (
        <div className="flex items-center justify-between rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          <span>{overdue.length} unfinished task(s) from earlier days</span>
          <button onClick={carryOver} className="font-medium underline">
            Carry over to today
          </button>
        </div>
      )}
      {notice && <p className="text-sm text-slate-500">{notice}</p>}
      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <TaskList
          tasks={tasks}
          empty="Nothing planned for today."
          onToggle={toggle}
          onDelete={remove}
          onAddSubtask={addSubtask}
        />
      )}
    </div>
  )
}
