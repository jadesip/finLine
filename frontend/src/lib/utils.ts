import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with proper precedence.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as currency.
 */
export function format_currency(
  value: number,
  currency: string = "USD",
  unit: string = "millions"
): string {
  const formatted = value.toLocaleString("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  const unit_suffix = unit === "millions" ? "M" : unit === "thousands" ? "K" : "";
  return `${formatted}${unit_suffix}`;
}

/**
 * Format a percentage.
 */
export function format_percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Parse a string to number, returning null if invalid.
 */
export function parse_number(value: string): number | null {
  const cleaned = value.replace(/[,$%]/g, "").trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? null : num;
}

/**
 * Get years from a data object with year keys.
 */
export function get_years(data: Record<string, any>): string[] {
  return Object.keys(data)
    .filter((key) => /^\d{4}$/.test(key))
    .sort();
}

/**
 * Debounce a function.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Set a nested value in an object using dot notation path
 */
export function set_nested_value<T extends Record<string, any>>(
  obj: T,
  path: string,
  value: any
): T {
  const keys = path.split(".");
  const result = { ...obj };
  let current: any = result;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    current[key] = current[key] ? { ...current[key] } : {};
    current = current[key];
  }

  current[keys[keys.length - 1]] = value;
  return result;
}

/**
 * Get a nested value from an object using dot notation path
 */
export function get_nested_value<T = any>(
  obj: Record<string, any>,
  path: string,
  default_value?: T
): T | undefined {
  const keys = path.split(".");
  let current: any = obj;

  for (const key of keys) {
    if (current === null || current === undefined) {
      return default_value;
    }
    current = current[key];
  }

  return current ?? default_value;
}
