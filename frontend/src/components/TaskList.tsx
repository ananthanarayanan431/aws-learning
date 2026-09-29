import { todayISO } from '../date'
import type { Task } from '../types'
import { TaskItem } from './TaskItem'

interface Props {
  tasks: Task[]
  empty: string
  onToggle: (task: Task) => void
  onDelete: (task: Task) => void
  onAddSubtask: (parent: Task, title: string) => Promise<void>
}

export function TaskList({ tasks, empty, ...handlers }: Props) {
  const today = todayISO()
  if (tasks.length === 0) return <p className="py-8 text-center text-sm text-slate-400">{empty}</p>
  return (
    <ul className="space-y-2">
      {tasks.map((t) => (
        <TaskItem key={t.id} task={t} today={today} {...handlers} />
      ))}
    </ul>
  )
}
