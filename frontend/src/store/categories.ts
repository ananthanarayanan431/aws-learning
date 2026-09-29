import { useEffect } from 'react'
import { create } from 'zustand'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { Category } from '../types'

const byName = (a: Category, b: Category) => a.name.localeCompare(b.name)

interface CategoryState {
  categories: Category[]
  loaded: boolean
  /** Fetches categories from the server once; later calls are no-ops unless `force` is set. */
  load: (force?: boolean) => Promise<void>
  /** Creates a category, or returns the existing one when the name is already taken. */
  add: (name: string) => Promise<Category>
  remove: (id: number) => Promise<void>
}

/**
 * Shared, app-wide category list. The server is the source of truth (categories live in
 * Postgres until deleted); this store just keeps every screen in sync without refetching.
 */
export const useCategoryStore = create<CategoryState>((set, get) => ({
  categories: [],
  loaded: false,

  load: async (force = false) => {
    if (get().loaded && !force) return
    try {
      set({ categories: await api.listCategories(), loaded: true })
    } catch {
      // Leave `loaded` false so the next consumer retries.
    }
  },

  add: async (name) => {
    try {
      const created = await api.createCategory(name)
      set((s) => ({ categories: [...s.categories, created].sort(byName) }))
      return created
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        await get().load(true)
        const existing = get().categories.find((c) => c.name.toLowerCase() === name.toLowerCase())
        if (existing) return existing
      }
      throw e
    }
  },

  remove: async (id) => {
    await api.deleteCategory(id)
    set((s) => ({ categories: s.categories.filter((c) => c.id !== id) }))
  },
}))

/** Hook for screens: triggers the initial load and returns the shared list. */
export function useCategories() {
  const categories = useCategoryStore((s) => s.categories)
  const load = useCategoryStore((s) => s.load)
  const add = useCategoryStore((s) => s.add)
  const remove = useCategoryStore((s) => s.remove)
  // The store dedupes via `loaded`, so every screen can call this safely.
  useEffect(() => {
    void load()
  }, [load])
  return { categories, addCategory: add, removeCategory: remove }
}
