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

