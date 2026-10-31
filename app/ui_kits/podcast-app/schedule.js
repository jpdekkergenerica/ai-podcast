/** Planning van een show: dagen (0 = maandag … 6 = zondag), tijd en tijdzone. Zie api/defaults.py. */
export const DAYS = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];

export const DEFAULT_SCHEDULE = { enabled: false, days: [0, 1, 2, 3, 4, 5, 6], time: "07:00", timezone: "Europe/Amsterdam" };

export function deviceTimezone(fallback = DEFAULT_SCHEDULE.timezone) {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || fallback; } catch { return fallback; }
}

/** Korte omschrijving voor in een lijst: "Uit", "Elke dag om 07:00", "Ma, wo, vr om 18:30". */
export function scheduleLabel(schedule) {
  const s = { ...DEFAULT_SCHEDULE, ...(schedule || {}) };
  if (!s.enabled) return "Handmatig";
  if (s.days.length === 7) return `Elke dag om ${s.time}`;
  const names = s.days.map((d, i) => (i === 0 ? DAYS[d] : DAYS[d].toLowerCase()));
  return `${names.join(", ")} om ${s.time}`;
}
