/** Planning van een podcast: dagen (0 = maandag … 6 = zondag), eigen interval, tijd en tijdzone. Zie api/defaults.py. */
export const DAYS = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];
export const DAY_NAMES = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"];
const MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"];

export const PRESETS = [
  { id: "daily", label: "Dagelijks" },
  { id: "weekdays", label: "Werkdagen" },
  { id: "weekly", label: "Wekelijks" },
  { id: "every", label: "Elke … dagen" },
];

export const DEFAULT_SCHEDULE = { enabled: true, days: [0, 1, 2, 3, 4, 5, 6], every_days: null, time: "07:00", timezone: "Europe/Amsterdam" };

export function deviceTimezone(fallback = DEFAULT_SCHEDULE.timezone) {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || fallback; } catch { return fallback; }
}

/** Welke voorinstelling hoort bij deze planning? */
export function presetOf(s) {
  if (s.every_days) return "every";
  if (s.days.length === 7) return "daily";
  if (s.days.length === 5 && s.days.every((d) => d < 5)) return "weekdays";
  if (s.days.length === 1) return "weekly";
  return "daily";
}

/** Planning voor een voorinstelling; behoudt tijd en tijdzone. */
export function applyPreset(s, preset, extra = {}) {
  const base = { ...s, every_days: null };
  if (preset === "daily") return { ...base, days: [0, 1, 2, 3, 4, 5, 6] };
  if (preset === "weekdays") return { ...base, days: [0, 1, 2, 3, 4] };
  if (preset === "weekly") return { ...base, days: [extra.day ?? (s.days.length === 1 ? s.days[0] : 0)] };
  return { ...base, days: [0, 1, 2, 3, 4, 5, 6], every_days: extra.every ?? s.every_days ?? 2 };
}

export function scheduleLabel(s) {
  const t = s.time;
  if (s.every_days) return `Elke ${s.every_days} dagen om ${t}`;
  const p = presetOf(s);
  if (p === "daily") return `Dagelijks om ${t}`;
  if (p === "weekdays") return `Werkdagen om ${t}`;
  if (p === "weekly") return `Elke ${DAY_NAMES[s.days[0]]} om ${t}`;
  return `${s.days.map((d) => DAYS[d].toLowerCase()).join(", ")} om ${t}`;
}

export const dateText = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : `${DAYS[(d.getDay() + 6) % 7].toLowerCase()} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
};

export const minutesText = (seconds) => `${Math.max(1, Math.round(seconds / 60))} min`;
