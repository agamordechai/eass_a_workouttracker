const STORAGE_KEY = 'bodyweight_kg';

export function getBodyweightKg(): number | null {
  const val = localStorage.getItem(STORAGE_KEY);
  if (!val) return null;
  const n = parseFloat(val);
  return isNaN(n) || n <= 0 ? null : n;
}

export function setBodyweightKg(kg: number | null): void {
  if (kg == null) {
    localStorage.removeItem(STORAGE_KEY);
  } else {
    localStorage.setItem(STORAGE_KEY, String(kg));
  }
}
