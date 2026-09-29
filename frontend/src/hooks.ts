import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { ApiError } from './api/client'
import type { Category, Task, TaskInput } from './types'

export function errorMessage(e: unknown): string {
  return e instanceof ApiError || e instanceof Error ? e.message : 'Unexpected error'
}

/** Loads a task list and exposes the mutations shared by every task view. */
export function useTasks(load: () => Promise<Task[]>) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      setTasks(await load())
      setError(null)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load])

  useEffect(() => {
    reload()
  }, [reload])

  const run = async (action: () => Promise<unknown>) => {
    try {
      await action()
      await reload()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  return {
    tasks,
    loading,
    error,
    reload,
    create: (input: TaskInput) => run(() => api.createTask(input)),
    toggle: (t: Task) => run(() => api.updateTask(t.id, { status: t.status === 'done' ? 'todo' : 'done' })),
    remove: (t: Task) => run(() => api.deleteTask(t.id)),
    addSubtask: (parent: Task, title: string) => run(() => api.createTask({ title, parent_id: parent.id })),
  }
}

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([])
  useEffect(() => {
    api.listCategories().then(setCategories, () => {})
  }, [])
  return categories
}
