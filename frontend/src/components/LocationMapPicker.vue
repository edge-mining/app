<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const latitude = defineModel<number>("latitude", { required: true });
const longitude = defineModel<number>("longitude", { required: true });

const mapContainer = ref<HTMLElement | null>(null);

let map: L.Map | null = null;
let marker: L.Marker | null = null;
// Guards updates coming from the map itself, to avoid a watch feedback loop.
let updatingFromMap = false;

// Edge Mining logo mark (from VectorIcon.vue), used as the map marker.
const BRAND_COLOR = "#BEFFA3";
const logoSvg = `<svg width="22" height="22" viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M31.825 13.917L43.6549 2.08496M2.085 13.917L13.915 2.08496M31.805 13.952V43.705M31.835 13.923H2.085M31.825 43.653L43.6549 31.821" stroke="${BRAND_COLOR}" stroke-width="4.17" stroke-miterlimit="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

const markerIcon = L.divIcon({
  className: "em-map-marker",
  iconSize: [40, 48],
  iconAnchor: [20, 48],
  popupAnchor: [0, -48],
  html: `
    <div style="position:relative;width:40px;height:48px;">
      <div style="position:absolute;top:0;left:0;width:40px;height:40px;border-radius:9999px;background:#171717;border:2px solid ${BRAND_COLOR};box-shadow:0 2px 6px rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;">
        ${logoSvg}
      </div>
      <div style="position:absolute;left:50%;bottom:0;transform:translateX(-50%);width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-top:10px solid ${BRAND_COLOR};"></div>
    </div>
  `,
});

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function setCoordinates(lat: number, lng: number) {
  updatingFromMap = true;
  latitude.value = round(lat);
  longitude.value = round(lng);
  updatingFromMap = false;
}

onMounted(() => {
  if (!mapContainer.value) return;

  const lat = latitude.value ?? 0;
  const lng = longitude.value ?? 0;

  map = L.map(mapContainer.value, { attributionControl: true }).setView([lat, lng], 6);

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }
  ).addTo(map);

  marker = L.marker([lat, lng], { draggable: true, icon: markerIcon }).addTo(map);

  marker.on("dragend", () => {
    if (!marker) return;
    const { lat: mLat, lng: mLng } = marker.getLatLng();
    setCoordinates(mLat, mLng);
  });

  map.on("click", (event: L.LeafletMouseEvent) => {
    marker?.setLatLng(event.latlng);
    setCoordinates(event.latlng.lat, event.latlng.lng);
  });

  // The container may be laid out after mount; recompute the size.
  setTimeout(() => map?.invalidateSize(), 0);
});

// Keep the marker in sync when the coordinates change from outside (e.g. loaded from the store).
watch([latitude, longitude], ([lat, lng]) => {
  if (updatingFromMap || !map || !marker || lat === undefined || lng === undefined) return;
  marker.setLatLng([lat, lng]);
  map.panTo([lat, lng]);
});

onBeforeUnmount(() => {
  map?.remove();
  map = null;
  marker = null;
});
</script>

<template>
  <div class="space-y-2">
    <div
      ref="mapContainer"
      class="h-72 w-full rounded-xl border border-base-300/40 overflow-hidden bg-neutral-900 z-0"
    ></div>
    <p class="text-sm text-base-content/60">
      Click on the map or drag the marker to set your location ·
      <span class="font-mono text-base-content/80">
        {{ latitude?.toFixed(4) }}, {{ longitude?.toFixed(4) }}
      </span>
    </p>
  </div>
</template>

<style scoped>
/* Match the dark UI: neutral controls and attribution. */
:deep(.leaflet-container) {
  background: #171717;
}

:deep(.leaflet-control-attribution) {
  background: rgba(0, 0, 0, 0.6);
  color: rgba(255, 255, 255, 0.6);
}

:deep(.leaflet-control-attribution a) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.leaflet-bar a) {
  background-color: #262626;
  color: #e5e5e5;
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

:deep(.leaflet-bar a:hover) {
  background-color: #333333;
}
</style>
