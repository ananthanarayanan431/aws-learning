import { useState } from 'react'
import { HealthBadge } from './components/HealthBadge'
import { CalendarPage } from './pages/CalendarPage'
import { TasksPage } from './pages/TasksPage'
import { TodayPage } from './pages/TodayPage'

const TABS = { today: 'Today', calendar: 'Calendar', all: 'All tasks' } as const
type Tab = keyof typeof TABS

export default function App() {
  const [tab, setTab] = useState<Tab>('today')
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className={`mx-auto space-y-4 p-4 ${tab === 'calendar' ? 'max-w-4xl' : 'max-w-2xl'}`}>
        <header className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Todo</h1>
          <HealthBadge />
        </header>
        <nav className="flex gap-1 border-b border-slate-200">
          {(Object.keys(TABS) as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`-mb-px border-b-2 px-3 py-2 text-sm ${
                tab === t ? 'border-indigo-600 font-medium text-indigo-600' : 'border-transparent text-slate-500'
              }`}
            >
              {TABS[t]}
            </button>
          ))}
        </nav>
        {tab === 'today' && <TodayPage />}
        {tab === 'calendar' && <CalendarPage />}
        {tab === 'all' && <TasksPage />}
      </div>
    </div>
  )
}
