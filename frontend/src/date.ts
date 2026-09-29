/** Today's local date as YYYY-MM-DD, matching the API's date format. */
export const todayISO = () => new Date().toLocaleDateString('en-CA')

/** Formats a Date as local YYYY-MM-DD (avoids the UTC shift of toISOString). */
export const toISO = (d: Date) => d.toLocaleDateString('en-CA')

/** The 6x7 grid of days shown for a month, starting on Monday. */
export function monthGrid(year: number, month: number): Date[] {
  const first = new Date(year, month, 1)
  const offset = (first.getDay() + 6) % 7 // Monday = 0
  return Array.from({ length: 42 }, (_, i) => new Date(year, month, 1 - offset + i))
}
