export type Status = 'todo' | 'in_progress' | 'done'
export type Priority = 'low' | 'medium' | 'high' | 'urgent'

export interface Category {
  id: number
  name: string
  color: string
}

export interface Tag {
  id: number
  name: string
}

export interface Task {
  id: number
  title: string
  description: string | null
  status: Status
  priority: Priority
  due_date: string | null
  planned_date: string | null
  completed_at: string | null
  category: Category | null
  tags: Tag[]
  parent_id: number | null
  subtasks: Task[]
}

export interface TaskInput {
  title: string
  description?: string | null
  status?: Status
  priority?: Priority
  due_date?: string | null
  planned_date?: string | null
  category_id?: number | null
  parent_id?: number | null
  tag_ids?: number[]
}

export interface SuccessResponse<T> {
  success: true
  message: string
  data: T
  meta: Record<string, unknown> | null
}

export interface ErrorResponse {
  success: false
  message: string
  error: { code: string; details?: unknown }
}
