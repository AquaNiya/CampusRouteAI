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

function startLiveLocation() {
    if (!activeDelivery || !navigator.geolocation) return toast("Create a delivery before sharing live location.");
    els.liveStart.classList.add("hidden");
    els.liveStop.classList.remove("hidden");
    els.liveStatus.textContent = "Requesting precise browser location…";
    liveWatch = navigator.geolocation.watchPosition(
        async (position) => {
            updateLiveMarker(
                position.coords.latitude,
                position.coords.longitude,
                position.coords.accuracy
            );
            try {
                await api("/api/live-location", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        delivery_id: activeDelivery.id,
                        campus_id: campusId,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy_m: position.coords.accuracy,
                        speed_mps: position.coords.speed || 0,
                        heading_degrees: position.coords.heading || 0,
                    }),
                });
            } catch (error) {
                els.liveStatus.textContent = `GPS shown locally; server update failed: ${error.message}`;
            }
        },
        (error) => {
            const messages = {
                1: "Location permission was denied. Allow location for localhost.",
                2: "Location is currently unavailable. Try again near a window.",
                3: "Location request timed out. Try again.",
            };
            els.liveStatus.textContent = messages[error.code] || "GPS permission unavailable.";
            els.liveStart.classList.remove("hidden");
            els.liveStop.classList.add("hidden");
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0,
        }
    );
}
function stopLiveLocation() { if (liveWatch !== undefined) navigator.geolocation.clearWatch(liveWatch); els.liveStart.classList.remove("hidden"); els.liveStop.classList.add("hidden"); els.liveStatus.textContent = "Live sharing stopped."; }

function toggleMapFullscreen() {
    const isFullscreen = els.mapPanel.classList.toggle("is-fullscreen");
    document.body.classList.toggle("map-fullscreen-open", isFullscreen);
    els.mapFullscreen.textContent = isFullscreen ? "✕ Exit full screen" : "⛶ Full screen";
    els.mapFullscreen.setAttribute("aria-pressed", String(isFullscreen));
    window.setTimeout(() => { if (leafletMap) leafletMap.invalidateSize(); }, 150);
}

els.campus.addEventListener("change", async () => { campusId = els.campus.value; try { await loadCampus(); } catch (error) { toast(error.message); } }); els.batteryRange.addEventListener("input", () => { els.batteryValue.textContent = `${els.batteryRange.value}%`; }); document.querySelectorAll("[data-priority]").forEach((button) => button.addEventListener("click", () => setPriority(button.dataset.priority))); $("routeButton").addEventListener("click", createDelivery); els.gps.addEventListener("click", useGps); els.gpsFallback.addEventListener("click", () => { if (lastGps) { els.start.value = lastGps.id; els.gpsMessage.textContent = `Using nearest campus point: ${lastGps.name}.`; } }); els.blockButton.addEventListener("click", blockRoad); els.addTask.addEventListener("click", addTaskRow); els.optimize.addEventListener("click", optimize); els.liveStart.addEventListener("click", startLiveLocation); els.liveStop.addEventListener("click", stopLiveLocation); els.confirm.addEventListener("click", confirmDelivery); els.cancel.addEventListener("click", () => terminalStatus("CANCELLED")); els.fail.addEventListener("click", () => terminalStatus("FAILED")); els.searchButton.addEventListener("click", searchLocation); els.search.addEventListener("keydown", (event) => { if (event.key === "Enter") searchLocation(); }); els.theme.addEventListener("click", () => document.body.classList.toggle("dark")); els.mapFullscreen.addEventListener("click", toggleMapFullscreen);

(async function init() { try { await loadCampuses(); } catch (error) { els.connection.textContent = "Offline"; els.connection.className = "status offline"; toast(`Backend unavailable: ${error.message}`); } })();

window.addEventListener("offline", () => { els.connection.textContent = "Offline mode"; els.connection.className = "status offline"; toast("Network is offline. Cached interface remains available.", "info"); });
window.addEventListener("online", () => { els.connection.textContent = "Network restored"; els.connection.className = "status online"; });
if ("serviceWorker" in navigator) navigator.serviceWorker.register("service-worker.js").catch(() => undefined);
