const API_BASE_URL = window.CAMPUSROUTE_CONFIG?.apiBase || "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);
const els = {
    campus: $("campusSelect"), start: $("startLocation"), destination: $("destination"), item: $("itemType"), receiver: $("receiverName"), note: $("deliveryNote"), accessible: $("accessibleOnly"),
    batteryRange: $("batteryPercentage"), batteryValue: $("batteryValue"), traffic: $("trafficLevel"), weather: $("weatherCondition"), routeButton: $("routeButton"),
    connection: $("connectionStatus"), mapTitle: $("mapTitle"), mapStatus: $("campusMapStatus"), area: $("campusArea"), description: $("campusDescription"), mapHint: $("campusMapHint"), search: $("locationSearch"), searchButton: $("searchLocationButton"),
    routeResult: $("routeResult"), status: $("resultStatus"), reason: $("decisionReason"), path: $("routePath"), distance: $("resultDistance"), eta: $("resultEta"), elevation: $("resultElevation"), strategy: $("resultStrategy"), batteryResult: $("resultBattery"), batteryBar: $("batteryBar"), batteryState: $("batteryState"), batteryWarning: $("batteryWarning"), delays: $("delayReasons"), analysis: $("algorithmAnalysis"),
    tracking: $("trackingCard"), trackingMessage: $("trackingMessage"), trackingLocation: $("trackingLocation"), trackingEta: $("trackingEta"), trackingBar: $("trackingProgressBar"), trackingText: $("trackingProgressText"), liveStart: $("startLiveButton"), liveStop: $("stopLiveButton"), liveStatus: $("liveLocationStatus"), cancel: $("cancelButton"), fail: $("failButton"), confirmationCode: $("confirmationCode"), confirm: $("confirmDeliveryButton"), proofMessage: $("proofMessage"),
    gps: $("gpsButton"), gpsFallback: $("gpsFallbackButton"), gpsMessage: $("gpsMessage"), blockedSource: $("blockedSource"), blockedDestination: $("blockedDestination"), incidentReason: $("incidentReason"), incidentSeverity: $("incidentSeverity"), blockButton: $("blockRoadButton"), blockMessage: $("blockMessage"), multiStart: $("multiStartLocation"), multiList: $("multiTaskList"), addTask: $("addTaskButton"), optimize: $("optimizeButton"), optimizeResult: $("optimizationResult"), optimizeSteps: $("optimizationSteps"), history: $("deliveryHistory"), theme: $("themeToggle"), toast: $("toastRegion")
};

let selectedPriority = "NORMAL";
let campusId = "demo";
let mapData = { locations: [], roads: [], boundary: [] };
let leafletMap;
let mapLayers;
let activeDelivery;
let lastGps;
let trackingTimer;
let liveWatch;
let robotTimer;

async function api(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    const data = await response.json();
    if (!response.ok) {
        const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(", ") : data.detail;
        throw new Error(detail || "Request could not be completed.");
    }
    return data;
}

function toast(message, kind = "error") {
    const item = document.createElement("div");
    item.className = `toast ${kind}`;
    item.textContent = message;
    els.toast.append(item);
    window.setTimeout(() => item.remove(), 4500);
}

function setOptions(select, items, placeholder) {
    select.replaceChildren();
    const first = document.createElement("option");
    first.value = "";
    first.textContent = placeholder;
    select.append(first);
    items.forEach((item) => {
        const option = document.createElement("option");
        option.value = item.id;
        option.textContent = item.name;
        select.append(option);
    });
}

function setPriority(priority) {
    selectedPriority = priority;
    document.querySelectorAll("[data-priority]").forEach((button) => button.classList.toggle("active", button.dataset.priority === priority));
}

function clearMapLayers() {
    if (mapLayers) mapLayers.clearLayers();
}

function roadColor(road) {
    if (road.blocked) return "#d94f4f";
    return { paved: "#61708a", gravel: "#b98545", mud: "#795548", steep: "#8e44ad" }[road.terrain] || "#61708a";
}

function drawMap(route = [], segments = []) {
    if (!window.L || !mapData.locations.length) return;
    if (!leafletMap) {
        leafletMap = L.map("campusMap", { zoomControl: true, scrollWheelZoom: false, preferCanvas: true });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors", maxZoom: 20 }).addTo(leafletMap);
        mapLayers = L.layerGroup().addTo(leafletMap);
    }
    clearMapLayers();
    window.clearInterval(robotTimer);
    const positions = new Map(mapData.locations.map((location) => [location.id, [location.latitude, location.longitude]]));
    if (mapData.boundary.length >= 3) L.polygon(mapData.boundary, { color: "#3a2e4f", weight: 2, fillColor: "#b7e4e5", fillOpacity: 0.18 }).addTo(mapLayers);
    mapData.roads.forEach((road) => {
        const from = positions.get(road.source); const to = positions.get(road.destination);
        if (!from || !to) return;
        L.polyline([from, to], { color: roadColor(road), weight: 4, opacity: 0.72, dashArray: road.blocked ? "8 8" : undefined }).bindTooltip(`${road.terrain} · ${road.distance} km`).addTo(mapLayers);
    });
    mapData.locations.forEach((location) => {
        L.circleMarker([location.latitude, location.longitude], { radius: 6, color: "#3a2e4f", weight: 2, fillColor: "#ffe8a3", fillOpacity: 1 }).bindTooltip(location.name, {
            permanent: true,
            direction: "top",
            className: "map-label-tooltip",
            offset: [0, -7],
        }).addTo(mapLayers);
    });
    const routePositions = route.map((id) => positions.get(id)).filter(Boolean);
    if (segments.length) {
        const segmentColors = ["#d94f4f", "#3a2e4f", "#0f766e", "#b45309", "#7c3aed"];
        segments.forEach((segment, index) => {
            const points = segment.path.map((id) => positions.get(id)).filter(Boolean);
            if (points.length > 1) {
                L.polyline(points, { color: segmentColors[index % segmentColors.length], weight: 7, opacity: 0.92 }).addTo(mapLayers);
            }
            const lastPoint = points.at(-1);
            if (lastPoint) {
                L.circleMarker(lastPoint, { radius: 10, color: "#fff", weight: 2, fillColor: segmentColors[index % segmentColors.length], fillOpacity: 1 }).bindTooltip(`${segment.sequence}. ${segment.kind} · ${segment.location_name}`, { permanent: true, direction: "right", className: "stop-label-tooltip" }).addTo(mapLayers);
            }
        });
    } else if (routePositions.length > 1) {
        L.polyline(routePositions, { color: "#d94f4f", weight: 7, opacity: 0.95 }).addTo(mapLayers);
    }
    if (routePositions.length > 1) {
        animateRobot(routePositions);
    }
    const bounds = mapData.boundary.length >= 3 ? mapData.boundary : mapData.locations.map((location) => [location.latitude, location.longitude]);
    leafletMap.fitBounds(bounds, { padding: [22, 22] });
}

function animateRobot(points) {
    let index = 0;
    const marker = L.circleMarker(points[0], { radius: 9, color: "#fff", weight: 3, fillColor: "#d94f4f", fillOpacity: 1 }).addTo(mapLayers);
    const move = () => {
        const delivered = index === points.length - 1;
        marker.setLatLng(points[index]);
        marker.setStyle({
            fillColor: delivered ? "#16a34a" : "#d94f4f",
            color: delivered ? "#166534" : "#fff",
        });
        if (!delivered) index += 1;
        if (delivered) window.clearInterval(robotTimer);
    };
    move();
    robotTimer = window.setInterval(move, 1400);
}

function searchLocation() {
    const query = els.search.value.trim().toLowerCase();
    if (!query) return toast("Enter a building, gate or service name.", "info");
    const location = mapData.locations.find((item) => `${item.name} ${item.id}`.toLowerCase().includes(query));
    if (!location || !leafletMap) return toast("That campus location was not found.");
    leafletMap.setView([location.latitude, location.longitude], Math.max(leafletMap.getZoom(), 17));
    L.popup().setLatLng([location.latitude, location.longitude]).setContent(location.name).openOn(leafletMap);
}

async function loadCampuses() {
    const campuses = await api("/api/campuses");
    els.campus.replaceChildren();
    campuses.forEach((campus) => { const option = document.createElement("option"); option.value = campus.id; option.textContent = campus.name; els.campus.append(option); });
    campusId = els.campus.value || "demo";
    await loadCampus();
}

async function loadCampus() {
    const [locations, map] = await Promise.all([api(`/api/locations?campus_id=${encodeURIComponent(campusId)}`), api(`/api/map?campus_id=${encodeURIComponent(campusId)}`)]);
    mapData = map;
    setOptions(els.start, locations, "Choose pickup point"); setOptions(els.destination, locations, "Choose destination"); setOptions(els.blockedSource, locations, "Blocked road source"); setOptions(els.blockedDestination, locations, "Blocked road destination"); setOptions(els.multiStart, locations, "Choose robot start");
    els.mapTitle.textContent = map.campus?.name || "Campus map"; els.area.textContent = map.campus?.area_acres ? `${map.campus.area_acres} acres` : "Demo map"; els.description.textContent = map.campus?.description || "Campus structure loaded."; els.mapStatus.textContent = `${map.campus?.map_status || "DEMO"} · ${locations.length} locations · ${map.roads.length} roads`; const openIncidents = (map.incidents || []).filter((incident) => incident.status === "OPEN").length; els.mapHint.textContent = `${map.campus?.source_note || "Use the map to inspect campus structure."}${openIncidents ? ` · ${openIncidents} open road incident${openIncidents === 1 ? "" : "s"}` : ""}`;
    drawMap(); await loadHistory();
    els.connection.textContent = "Connected"; els.connection.className = "status online";
    els.multiList.replaceChildren(); addTaskRow();
}

function locationOptions() { return mapData.locations; }

function addTaskRow() {
    if (els.multiList.children.length >= 5) return toast("Maximum five delivery tasks allowed.", "info");
    const row = document.createElement("div"); row.className = "task-row";
    const pickup = document.createElement("select"); const drop = document.createElement("select"); const priority = document.createElement("select");
    setOptions(pickup, locationOptions(), "Pickup"); setOptions(drop, locationOptions(), "Drop-off");
    [["NORMAL", "Normal"], ["HIGH", "High"], ["EMERGENCY", "Emergency"]].forEach(([value, text]) => { const option = document.createElement("option"); option.value = value; option.textContent = text; priority.append(option); });
    row.append(pickup, drop, priority); els.multiList.append(row);
}

async function createDelivery() {
    if (!els.start.value || !els.destination.value) return toast("Choose pickup and destination first.");
    if (els.start.value === els.destination.value) return toast("Pickup and destination must be different.");
    els.routeButton.disabled = true; els.routeButton.firstChild.textContent = "Planning… ";
    try {
        const data = await api("/api/deliveries", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ campus_id: campusId, pickup_location: els.start.value, destination: els.destination.value, item_type: els.item.value, priority: selectedPriority, emergency: selectedPriority === "EMERGENCY", accessible_only: els.accessible.checked, battery_percentage: Number(els.batteryRange.value), traffic: els.traffic.value, weather: els.weather.value, receiver_name: els.receiver.value.trim() || null, delivery_note: els.note.value.trim() || null }) });
        showDelivery(data);
        await loadHistory();
    } catch (error) { toast(error.message); } finally { els.routeButton.disabled = false; els.routeButton.firstChild.textContent = "Plan my delivery "; }
}

function showDelivery(data) {
    const route = data.route; activeDelivery = data; els.routeResult.classList.remove("hidden"); setDeliveryStatus(data.status); els.reason.textContent = route.selection_reason; els.path.textContent = route.path_names.join("  →  "); els.distance.textContent = `${route.distance_km} km`; els.eta.textContent = `${route.estimated_time_minutes} min`; els.elevation.textContent = `${route.elevation_gain_m} m`; els.strategy.textContent = `${route.algorithm} · ${route.strategy.replaceAll("_", " ")}`; els.batteryResult.textContent = `${route.remaining_battery}%`; els.batteryBar.style.width = `${Math.max(0, Math.min(100, route.remaining_battery))}%`; els.batteryState.textContent = route.battery_state ? `${route.battery_state.label}: ${route.battery_state.message}` : "Battery state unavailable."; els.batteryWarning.textContent = route.battery_warning ? "Low battery reserve: charge before another delivery." : "Battery feasibility check passed."; els.delays.textContent = route.delay_reasons.length ? `Delay factors: ${route.delay_reasons.join(" ")}` : "No additional delay detected."; els.proofMessage.textContent = data.demo_confirmation_code ? `Demo receiver code: ${data.demo_confirmation_code}. In production this is sent privately to the receiver.` : "Ask the receiver for the confirmation code."; if (data.demo_confirmation_code) els.confirmationCode.value = data.demo_confirmation_code; renderAnalysis(route.algorithm_analysis); drawMap(route.path); startDemoTracking(data); els.routeResult.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setDeliveryStatus(status) {
    els.status.textContent = status;
    els.status.className = status === "DELIVERED" ? "success-chip delivered-chip" : "success-chip";
}

async function persistDeliveryStatus(status) {
    if (!activeDelivery) return;
    try {
        const updated = await api(`/api/deliveries/${activeDelivery.id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        activeDelivery = updated;
        setDeliveryStatus(updated.status);
        await loadHistory();
    } catch (error) {
        toast(`Status update failed: ${error.message}`);
    }
}

async function confirmDelivery() {
    if (!activeDelivery) return toast("Create a delivery first.");
    const code = els.confirmationCode.value.trim();
    if (code.length !== 6) return toast("Enter the six-digit receiver confirmation code.");
    try {
        const updated = await api(`/api/deliveries/${activeDelivery.id}/confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmation_code: code }),
        });
        activeDelivery = updated;
        setDeliveryStatus(updated.status);
        els.proofMessage.textContent = "Delivery confirmed with receiver proof.";
        els.trackingMessage.textContent = "Delivery completed and proof of delivery recorded.";
        window.clearInterval(trackingTimer);
        drawMap(activeDelivery.route?.path || []);
        await loadHistory();
    } catch (error) {
        els.proofMessage.textContent = error.message;
        toast(error.message);
    }
}

async function terminalStatus(status) {
    if (!activeDelivery) return toast("Create a delivery first.");
    window.clearInterval(trackingTimer);
    await persistDeliveryStatus(status);
    els.trackingMessage.textContent = status === "CANCELLED" ? "Delivery cancelled." : "Delivery marked as failed; human review required.";
}

function renderAnalysis(analysis) {
    els.analysis.replaceChildren(); const table = document.createElement("table"); table.className = "analysis-table"; const head = document.createElement("tr"); ["Search", "Result", "Cost", "Why"].forEach((text) => { const cell = document.createElement("th"); cell.textContent = text; head.append(cell); }); table.append(head);
    Object.entries(analysis).forEach(([name, result]) => { const row = document.createElement("tr"); if (result.selected) row.className = "selected-row"; [result.selected ? `${name} ✓` : name, result.found ? `${result.distance_km} km` : "No route", result.found ? `${result.total_cost ?? "—"}` : "—", result.note || (result.battery_insufficient ? "Battery insufficient" : "—")].forEach((text) => { const cell = document.createElement("td"); cell.textContent = text; row.append(cell); }); table.append(row); }); els.analysis.append(table);
}

function startDemoTracking(data) {
    window.clearInterval(trackingTimer); els.tracking.classList.remove("hidden"); const route = data.route.path_names; let index = 0; let statusStarted = activeDelivery?.status !== "CREATED"; const update = () => { const percent = Math.round((index / Math.max(1, route.length - 1)) * 100); els.trackingLocation.textContent = route[index] || "Delivered"; els.trackingEta.textContent = percent >= 100 ? "Delivered" : `${Math.max(1, data.route.estimated_time_minutes - Math.round(data.route.estimated_time_minutes * percent / 100))} min left`; els.trackingText.textContent = `${percent}%`; els.trackingBar.style.width = `${percent}%`; els.trackingMessage.textContent = percent >= 100 ? "Delivery completed in simulation." : "Robot is following the planned route."; if (!statusStarted) { statusStarted = true; void persistDeliveryStatus("ASSIGNED"); } else if (percent >= 100) { window.clearInterval(trackingTimer); void persistDeliveryStatus("IN_TRANSIT").then(() => persistDeliveryStatus("DELIVERED")); } else if (index > 0) { void persistDeliveryStatus("IN_TRANSIT"); } if (index < route.length - 1) index += 1; }; update(); trackingTimer = window.setInterval(update, 1800); }

async function useGps() {
    if (!navigator.geolocation) return toast("This browser does not support GPS.");
    els.gpsMessage.textContent = "Detecting your nearest campus point…";
    navigator.geolocation.getCurrentPosition(async (position) => { try { const query = new URLSearchParams({ latitude: position.coords.latitude, longitude: position.coords.longitude, campus_id: campusId }); const nearest = await api(`/api/nearest?${query}`); lastGps = nearest; els.start.value = nearest.id; els.gpsFallback.classList.toggle("hidden", nearest.within_campus); els.gpsMessage.textContent = nearest.within_campus ? `Pickup detected near ${nearest.name}.` : `Outside campus; nearest point is ${nearest.name}.`; } catch (error) { toast(error.message); } }, () => { els.gpsMessage.textContent = "GPS permission unavailable. Choose a pickup manually."; }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
}

async function loadHistory() { try { const records = await api("/api/deliveries?limit=8&offset=0"); els.history.replaceChildren(); if (!records.length) { const empty = document.createElement("p"); empty.className = "hint"; empty.textContent = "No deliveries yet."; els.history.append(empty); return; } records.slice().reverse().forEach((record) => { const item = document.createElement("div"); item.className = "history-item"; const title = document.createElement("strong"); title.textContent = `${record.item_type} · ${record.status}`; const info = document.createElement("span"); info.textContent = `${record.pickup_location} → ${record.destination}`; item.append(title, info); els.history.append(item); }); } catch (error) { toast(error.message); } }

async function blockRoad() { if (!els.blockedSource.value || !els.blockedDestination.value) return toast("Choose both ends of the road."); try { const result = await api("/api/roads/block", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ campus_id: campusId, source: els.blockedSource.value, destination: els.blockedDestination.value, reason: els.incidentReason.value.trim() || "Road incident reported by operator", severity: els.incidentSeverity.value }) }); els.blockMessage.textContent = `${result.message} ${result.incident.reason}`; await loadCampus(); if (activeDelivery) { const replanned = await api(`/api/deliveries/${activeDelivery.id}/replan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_location: activeDelivery.pickup_location, battery_percentage: Number(els.batteryRange.value), traffic: els.traffic.value, weather: els.weather.value }) }); showDelivery(replanned); toast("Blocked road detected. Route re-planned automatically.", "info"); } } catch (error) { toast(error.message); } }

function renderOptimizationSteps(result) {
    els.optimizeSteps.replaceChildren();
    const sequence = document.createElement("p");
    sequence.className = "hint";
    sequence.textContent = `Stop order: ${result.stop_order.join(" → ")}`;
    els.optimizeSteps.append(sequence);
    result.delivery_battery_summary.forEach((summary) => {
        const card = document.createElement("div");
        card.className = `optimization-step ${summary.battery_state.level.toLowerCase()}`;
        const title = document.createElement("strong");
        title.textContent = `${summary.task_id} · ${summary.priority}`;
        const details = document.createElement("span");
        details.textContent = `${summary.distance_km} km · ${summary.estimated_time_minutes} min · battery ${summary.battery_before}% → ${summary.battery_after}%`;
        const state = document.createElement("b");
        state.textContent = summary.battery_state.label;
        card.append(title, details, state);
        els.optimizeSteps.append(card);
    });
}

async function optimize() { const rows = [...els.multiList.children]; const tasks = rows.map((row) => { const selects = row.querySelectorAll("select"); return { pickup_location: selects[0].value, destination: selects[1].value, item_type: "OTHER", priority: selects[2].value }; }); if (!els.multiStart.value || tasks.some((task) => !task.pickup_location || !task.destination)) return toast("Choose start, pickup and drop-off for every task."); try { const result = await api("/api/deliveries/optimize", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ campus_id: campusId, starting_location: els.multiStart.value, tasks, battery_percentage: Number(els.batteryRange.value), traffic: els.traffic.value, weather: els.weather.value }) }); els.optimizeResult.classList.remove("hidden"); els.optimizeResult.textContent = `${result.why_order} Total: ${result.total_distance} km · ${result.estimated_time_minutes} min · final battery ${result.final_battery.percentage}% (${result.final_battery.label}).`; renderOptimizationSteps(result); drawMap(result.combined_route, result.delivery_segments); toast("Multiple-delivery plan is now visible on the campus map.", "info"); document.querySelector(".map-panel").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (error) { toast(error.message); } }

function startLiveLocation() { if (!activeDelivery || !navigator.geolocation) return toast("Create a delivery before sharing live location."); els.liveStart.classList.add("hidden"); els.liveStop.classList.remove("hidden"); els.liveStatus.textContent = "Sharing live location for this delivery."; liveWatch = navigator.geolocation.watchPosition(async (position) => { try { await api("/api/live-location", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ delivery_id: activeDelivery.id, campus_id: campusId, latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy_m: position.coords.accuracy, speed_mps: position.coords.speed || 0, heading_degrees: position.coords.heading || 0 }) }); } catch (error) { els.liveStatus.textContent = error.message; } }, () => { els.liveStatus.textContent = "GPS permission unavailable."; }); }
function stopLiveLocation() { if (liveWatch !== undefined) navigator.geolocation.clearWatch(liveWatch); els.liveStart.classList.remove("hidden"); els.liveStop.classList.add("hidden"); els.liveStatus.textContent = "Live sharing stopped."; }

els.campus.addEventListener("change", async () => { campusId = els.campus.value; try { await loadCampus(); } catch (error) { toast(error.message); } }); els.batteryRange.addEventListener("input", () => { els.batteryValue.textContent = `${els.batteryRange.value}%`; }); document.querySelectorAll("[data-priority]").forEach((button) => button.addEventListener("click", () => setPriority(button.dataset.priority))); $("routeButton").addEventListener("click", createDelivery); els.gps.addEventListener("click", useGps); els.gpsFallback.addEventListener("click", () => { if (lastGps) { els.start.value = lastGps.id; els.gpsMessage.textContent = `Using nearest campus point: ${lastGps.name}.`; } }); els.blockButton.addEventListener("click", blockRoad); els.addTask.addEventListener("click", addTaskRow); els.optimize.addEventListener("click", optimize); els.liveStart.addEventListener("click", startLiveLocation); els.liveStop.addEventListener("click", stopLiveLocation); els.confirm.addEventListener("click", confirmDelivery); els.cancel.addEventListener("click", () => terminalStatus("CANCELLED")); els.fail.addEventListener("click", () => terminalStatus("FAILED")); els.searchButton.addEventListener("click", searchLocation); els.search.addEventListener("keydown", (event) => { if (event.key === "Enter") searchLocation(); }); els.theme.addEventListener("click", () => document.body.classList.toggle("dark"));

(async function init() { try { await loadCampuses(); } catch (error) { els.connection.textContent = "Offline"; els.connection.className = "status offline"; toast(`Backend unavailable: ${error.message}`); } })();

window.addEventListener("offline", () => { els.connection.textContent = "Offline mode"; els.connection.className = "status offline"; toast("Network is offline. Cached interface remains available.", "info"); });
window.addEventListener("online", () => { els.connection.textContent = "Network restored"; els.connection.className = "status online"; });
if ("serviceWorker" in navigator) navigator.serviceWorker.register("service-worker.js").catch(() => undefined);
