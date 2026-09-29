import { useState } from 'react'
import { errorMessage } from '../hooks'
import type { Category } from '../types'

interface Props {
  categories: Category[]
  onDelete: (category: Category) => Promise<void>
}

/** Lists saved categories as chips; deleting one keeps its tasks but clears their category. */
export function CategoryManager({ categories, onDelete }: Props) {
  const [error, setError] = useState<string | null>(null)
  if (categories.length === 0) return null

  async function remove(c: Category) {
    if (!window.confirm(`Delete category "${c.name}"? Its tasks will be kept without a category.`)) return
    try {
      await onDelete(c)
      setError(null)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  return (
    <div className="space-y-1">
      <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
        <span>Categories:</span>
        {categories.map((c) => (
          <span key={c.id} className="flex items-center gap-1 rounded-full border border-slate-200 bg-white py-0.5 pl-2 pr-1">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: c.color }} />
            {c.name}
            <button
              type="button"
              aria-label={`Delete category ${c.name}`}
              onClick={() => remove(c)}
              className="rounded-full px-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      {error && <p className="text-xs text-rose-600">{error}</p>}
    </div>
  )
}
