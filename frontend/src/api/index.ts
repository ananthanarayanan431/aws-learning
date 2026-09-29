import type { Category, Tag, Task, TaskInput } from '../types'
import { request } from './client'

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
})

export const api = {
  health: () => request<{ status: string; service: string }>('/health'),
  healthDb: () => request<{ status: string; service: string }>('/health/db'),

  today: () => request<Task[]>('/today').then((r) => r.data),
  carryOver: () => request<{ moved: number }>('/today/carry-over', json('POST')).then((r) => r.data),

  listTasks: (params: Record<string, string> = {}) =>
    request<Task[]>('/tasks?' + new URLSearchParams(params)).then((r) => r.data),
  createTask: (input: TaskInput) => request<Task>('/tasks', json('POST', input)).then((r) => r.data),
  updateTask: (id: number, patch: Partial<TaskInput>) =>
    request<Task>(`/tasks/${id}`, json('PATCH', patch)).then((r) => r.data),
  deleteTask: (id: number) => request<null>(`/tasks/${id}`, json('DELETE')),

  listCategories: () => request<Category[]>('/categories').then((r) => r.data),
  createCategory: (name: string, color?: string) =>
    request<Category>('/categories', json('POST', { name, color })).then((r) => r.data),
  deleteCategory: (id: number) => request<null>(`/categories/${id}`, json('DELETE')),
  listTags: () => request<Tag[]>('/tags').then((r) => r.data),
  createTag: (name: string) => request<Tag>('/tags', json('POST', { name })).then((r) => r.data),
}
