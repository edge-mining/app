export function formatTimeAgo(date: string | Date, compact = true): string {
  const diffMs = Date.now() - new Date(date).getTime();
  if (diffMs < 0) return 'just now';
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  if (compact) {
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `~${days}d ago`;
    }
    if (hours > 0) return `~${hours}h ago`;
    if (minutes > 0) return `~${minutes}min ago`;
    return `${seconds}s ago`;
  }
  if (hours > 0) {
    const remMin = minutes % 60;
    return remMin > 0 ? `${hours}h and ${remMin}min ago` : `${hours}h ago`;
  }
  if (minutes > 0) {
    const remSec = seconds % 60;
    return remSec > 0 ? `${minutes}min and ${remSec}s ago` : `${minutes}min ago`;
  }
  return `${seconds}s ago`;
}

export function formatType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatPower(watts: number | undefined): string {
  if (watts === undefined || watts === null) return "-";
  if (watts >= 1000000) return `${(watts / 1000000).toFixed(1)} MW`;
  if (watts >= 1000) return `${(watts / 1000).toFixed(1)} kW`;
  return `${watts} W`;
}

export function formatCapacity(wh: number | undefined): string {
  if (wh === undefined || wh === null) return "-";
  if (wh >= 1000000) return `${(wh / 1000000).toFixed(1)} MWh`;
  if (wh >= 1000) return `${(wh / 1000).toFixed(1)} kWh`;
  return `${wh} Wh`;
}

export function formatHashRate(value?: number, unit?: string): string {
  if (!value) return "-";
  return `${value} ${unit || ""}`;
}

export function normalizeHashRate(value: number, unit: string): number {
  const multipliers: Record<string, number> = {
    "H/s": 1e-12,
    "KH/s": 1e-9,
    "MH/s": 1e-6,
    "GH/s": 1e-3,
    "TH/s": 1,
    "PH/s": 1e3,
    "EH/s": 1e6,
  };
  return value * (multipliers[unit] || 1);
}

