/**
 * ============================================================
 *  ENERGY DASHBOARD — GitHub Template
 *  Stack: React + Recharts + Tailwind (CDN)
 * ============================================================
 *
 *  INFLUXDB CONFIGURATION
 *  ──────────────────────
 *  Fill in the constants below to connect to your InfluxDB instance.
 *  All data-fetching functions are labelled with:
 *    //  ⬇ IMPORT DATA HERE
 *  so you can grep for them easily.
 *
 *  Required InfluxDB details:
 *    INFLUX_URL    – e.g. "http://localhost:8086"
 *    INFLUX_TOKEN  – your read-only API token
 *    INFLUX_ORG    – your organisation name or ID
 *    INFLUX_BUCKET – the bucket that holds your energy data
 *
 *  Measurement / field assumptions (edit to match your schema):
 *    measurement: "home_sensors"
 *      field "actual_temp"   – current indoor temperature (°F)
 *      field "set_temp"      – thermostat set-point (°F)
 *    measurement: "energy"
 *      field "predicted_bill"– running predicted monthly bill ($)
 */

// ─── INFLUXDB CONNECTION SETTINGS ────────────────────────────────────────────
const INFLUX_URL    = "YOUR_INFLUXDB_URL";      // e.g. "http://localhost:8086"
const INFLUX_TOKEN  = "YOUR_INFLUXDB_TOKEN";    // InfluxDB API token
const INFLUX_ORG    = "YOUR_ORG";               // organisation name or ID
const INFLUX_BUCKET = "YOUR_BUCKET";            // bucket name
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";

// ─── TIME RANGE OPTIONS ───────────────────────────────────────────────────────
const TIME_RANGES = [
  { label: "Last 24 Hours", flux: "-24h" },
  { label: "Last 3 Days",   flux: "-3d"  },
  { label: "Last Week",     flux: "-7d"  },
  { label: "Last Month",    flux: "-30d" },
  { label: "Last 3 Months", flux: "-90d" },
  { label: "Last Year",     flux: "-365d"},
];

// ─── INFLUXDB QUERY HELPER ────────────────────────────────────────────────────
/**
 * Runs a Flux query against InfluxDB and returns an array of
 * { time: string, value: number } objects ready for Recharts.
 *
 * @param {string} fluxQuery  – full Flux query string
 * @returns {Promise<Array>}
 */
async function queryInflux(fluxQuery) {
  // ⬇ IMPORT DATA HERE — replace this block with your InfluxDB client if preferred
  const response = await fetch(`${INFLUX_URL}/api/v2/query?org=${INFLUX_ORG}`, {
    method: "POST",
    headers: {
      "Authorization": `Token ${INFLUX_TOKEN}`,
      "Content-Type":  "application/vnd.flux",
      "Accept":        "application/csv",
    },
    body: fluxQuery,
  });
  if (!response.ok) throw new Error(`InfluxDB error: ${response.statusText}`);
  const csv  = await response.text();
  const rows = csv.trim().split("\n").slice(1); // drop header
  return rows
    .filter(r => r && !r.startsWith("#"))
    .map(row => {
      const cols = row.split(",");
      return { time: cols[5], value: parseFloat(cols[6]) };
    })
    .filter(r => !isNaN(r.value));
}

/**
 * Build a Flux query for a single field over a time range.
 * Edit the measurement name / field to match your schema.
 */
function buildFluxQuery(measurement, field, range) {
  // ⬇ IMPORT DATA HERE — adjust measurement, field, and any filters as needed
  return `
from(bucket: "${INFLUX_BUCKET}")
  |> range(start: ${range})
  |> filter(fn: (r) => r._measurement == "${measurement}" and r._field == "${field}")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
  `.trim();
}

// ─── PLACEHOLDER DATA (used when InfluxDB is not yet connected) ───────────────
function makePlaceholder(points = 24) {
  return Array.from({ length: points }, (_, i) => ({
    time:  `T-${points - i}h`,
    value: +(Math.random() * 10 + 68).toFixed(1),
  }));
}

// ─────────────────────────────────────────────────────────────────────────────
//  SUBCOMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

/** Navigation tab bar */
function TabBar({ current, onSelect }) {
  const tabs = ["Overview", "Appliance Consumption", "Comparative Data", "Data Retrieval"];
  return (
    <div style={{
      display: "flex", gap: 2, background: "#0f1923",
      borderBottom: "1px solid #1e3a5f", padding: "0 24px",
    }}>
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => onSelect(tab)}
          style={{
            padding: "14px 22px",
            background: "none",
            border: "none",
            borderBottom: current === tab ? "2px solid #00d4ff" : "2px solid transparent",
            color: current === tab ? "#00d4ff" : "#7a9bb5",
            fontFamily: "'Rajdhani', sans-serif",
            fontSize: 15,
            fontWeight: 600,
            letterSpacing: 1,
            cursor: "pointer",
            transition: "color 0.2s",
            textTransform: "uppercase",
          }}
        >{tab}</button>
      ))}
    </div>
  );
}

/** Historical data detail view (graph + time range + back button) */
function HistoricalView({ title, measurement, field, onBack }) {
  const [range,    setRange]    = useState(TIME_RANGES[0]);
  const [data,     setData]     = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // ⬇ IMPORT DATA HERE
      const query  = buildFluxQuery(measurement, field, range.flux);
      const result = await queryInflux(query);
      setData(result.length ? result : makePlaceholder());
    } catch (e) {
      console.warn("InfluxDB not connected — showing placeholder data.", e.message);
      setData(makePlaceholder());
      setError("InfluxDB not connected. Showing placeholder data.");
    } finally {
      setLoading(false);
    }
  }, [measurement, field, range]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div style={{ padding: 28, flex: 1 }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={onBack}
            style={{
              background: "none", border: "1px solid #1e3a5f", borderRadius: 6,
              color: "#00d4ff", cursor: "pointer", padding: "6px 14px",
              fontFamily: "'Rajdhani', sans-serif", fontSize: 18, lineHeight: 1,
            }}
          >← Back</button>
          <h2 style={{ margin: 0, color: "#e8f4f8", fontFamily: "'Rajdhani', sans-serif", fontSize: 22, letterSpacing: 2 }}>
            {title}
          </h2>
        </div>

        {/* Time Range dropdown */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ color: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 13, letterSpacing: 1 }}>TIME RANGE</span>
          <select
            value={range.label}
            onChange={e => setRange(TIME_RANGES.find(r => r.label === e.target.value))}
            style={{
              background: "#0f1923", border: "1px solid #1e3a5f", borderRadius: 6,
              color: "#00d4ff", padding: "7px 12px",
              fontFamily: "'Rajdhani', sans-serif", fontSize: 14, cursor: "pointer",
            }}
          >
            {TIME_RANGES.map(r => <option key={r.label}>{r.label}</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div style={{ background: "#1a2f1a", border: "1px solid #2d5a2d", borderRadius: 8, padding: "10px 16px", marginBottom: 20, color: "#6fbf6f", fontFamily: "'Rajdhani', sans-serif", fontSize: 13 }}>
          ⚠ {error}
        </div>
      )}

      {loading ? (
        <div style={{ color: "#7a9bb5", textAlign: "center", paddingTop: 80, fontFamily: "'Rajdhani', sans-serif", fontSize: 18 }}>
          Loading data…
        </div>
      ) : (
        <div style={{ background: "#0d1e2e", border: "1px solid #1e3a5f", borderRadius: 12, padding: 24 }}>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" />
              <XAxis dataKey="time" tick={{ fill: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 11 }} />
              <YAxis tick={{ fill: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#0f1923", border: "1px solid #00d4ff", borderRadius: 8, fontFamily: "'Rajdhani', sans-serif" }}
                labelStyle={{ color: "#7a9bb5" }}
                itemStyle={{ color: "#00d4ff" }}
              />
              <Line type="monotone" dataKey="value" stroke="#00d4ff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

/**
 * Data Box — a selectable card showing a current value.
 * When clicked it navigates to the HistoricalView for that dataset.
 */
function DataBox({ label, value, unit, measurement, field, onSelect, size = "normal" }) {
  const isLarge = size === "large";
  return (
    <button
      onClick={() => onSelect({ label, measurement, field })}
      style={{
        background: "linear-gradient(135deg, #0d1e2e 60%, #0f2a3f)",
        border: "1px solid #1e3a5f",
        borderRadius: 14,
        padding: isLarge ? "32px 40px" : "24px 32px",
        cursor: "pointer",
        textAlign: "left",
        flex: isLarge ? "1.4" : "1",
        transition: "border-color 0.2s, transform 0.15s",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = "#00d4ff"; e.currentTarget.style.transform = "translateY(-2px)"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e3a5f"; e.currentTarget.style.transform = "translateY(0)"; }}
    >
      {/* subtle glow accent */}
      <div style={{ position: "absolute", top: -30, right: -30, width: 120, height: 120, background: "radial-gradient(circle, rgba(0,212,255,0.07) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ color: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 12, letterSpacing: 2, textTransform: "uppercase", marginBottom: 10 }}>
        {label}
      </div>
      <div style={{ color: "#e8f4f8", fontFamily: "'Rajdhani', sans-serif", fontSize: isLarge ? 48 : 38, fontWeight: 700, lineHeight: 1 }}>
        {value !== null && value !== undefined ? `${value}${unit}` : "—"}
      </div>
      <div style={{ color: "#00d4ff", fontFamily: "'Rajdhani', sans-serif", fontSize: 11, letterSpacing: 1, marginTop: 12, opacity: 0.7 }}>
        TAP TO VIEW HISTORY →
      </div>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  PAGES
// ─────────────────────────────────────────────────────────────────────────────

function OverviewPage() {
  // Current values fetched from InfluxDB
  const [actualTemp,     setActualTemp]     = useState(null);
  const [setTemp,        setSetTemp]        = useState(null);
  const [predictedBill,  setPredictedBill]  = useState(null);
  const [historicalView, setHistoricalView] = useState(null); // { label, measurement, field }

  useEffect(() => {
    // ⬇ IMPORT DATA HERE — fetch latest single values from InfluxDB
    async function fetchCurrentValues() {
      try {
        const latestQuery = (measurement, field) => `
from(bucket: "${INFLUX_BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "${measurement}" and r._field == "${field}")
  |> last()
        `.trim();

        const [aTemp, sTemp, bill] = await Promise.all([
          queryInflux(latestQuery("home_sensors", "actual_temp")),
          queryInflux(latestQuery("home_sensors", "set_temp")),
          queryInflux(latestQuery("energy", "predicted_bill")),
        ]);
        if (aTemp.length) setActualTemp(aTemp[0].value.toFixed(1));
        if (sTemp.length) setSetTemp(sTemp[0].value.toFixed(1));
        if (bill.length)  setPredictedBill(bill[0].value.toFixed(2));
      } catch {
        // InfluxDB not configured yet — leave as null (shows "—")
      }
    }
    fetchCurrentValues();
  }, []);

  if (historicalView) {
    return (
      <HistoricalView
        title={historicalView.label}
        measurement={historicalView.measurement}
        field={historicalView.field}
        onBack={() => setHistoricalView(null)}
      />
    );
  }

  return (
    <div style={{ padding: 32 }}>
      <h2 style={{ color: "#e8f4f8", fontFamily: "'Rajdhani', sans-serif", fontSize: 13, letterSpacing: 3, textTransform: "uppercase", margin: "0 0 28px", color: "#7a9bb5" }}>
        Home at a Glance
      </h2>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* ── Data Box: Actual Temperature ── */}
        <DataBox
          label="Actual Temperature"
          value={actualTemp}
          unit="°F"
          measurement="home_sensors"   // ⬅ edit to match your InfluxDB measurement
          field="actual_temp"          // ⬅ edit to match your InfluxDB field
          onSelect={setHistoricalView}
        />

        {/* ── Data Box: Set Temperature ── */}
        <DataBox
          label="Set Temperature"
          value={setTemp}
          unit="°F"
          measurement="home_sensors"   // ⬅ edit to match your InfluxDB measurement
          field="set_temp"             // ⬅ edit to match your InfluxDB field
          onSelect={setHistoricalView}
        />

        {/* ── Predicted Bill (larger, non-selectable summary card) ── */}
        <div style={{
          background: "linear-gradient(135deg, #0d1e2e 60%, #0f2a3f)",
          border: "1px solid #1e3a5f",
          borderRadius: 14,
          padding: "32px 40px",
          flex: "1.4",
          position: "relative",
          overflow: "hidden",
        }}>
          <div style={{ position: "absolute", top: -30, right: -30, width: 160, height: 160, background: "radial-gradient(circle, rgba(0,255,180,0.06) 0%, transparent 70%)", pointerEvents: "none" }} />
          <div style={{ color: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 12, letterSpacing: 2, textTransform: "uppercase", marginBottom: 10 }}>
            Predicted Monthly Bill
          </div>
          <div style={{ color: "#e8f4f8", fontFamily: "'Rajdhani', sans-serif", fontSize: 52, fontWeight: 700, lineHeight: 1 }}>
            {predictedBill !== null ? `$${predictedBill}` : "—"}
          </div>
          <div style={{ color: "#7a9bb5", fontFamily: "'Rajdhani', sans-serif", fontSize: 12, marginTop: 12 }}>
            Estimated cost from the 1st to end of this month
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── PLACEHOLDER PAGES (populate in future chats) ────────────────────────────

function PlaceholderPage({ title }) {
  return (
    <div style={{ padding: 32 }}>
      <div style={{
        border: "1px dashed #1e3a5f", borderRadius: 14, padding: 48,
        textAlign: "center", color: "#3a5f7a",
        fontFamily: "'Rajdhani', sans-serif", fontSize: 16, letterSpacing: 1,
      }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>📋</div>
        <div style={{ textTransform: "uppercase", letterSpacing: 2 }}>{title}</div>
        <div style={{ fontSize: 13, marginTop: 8 }}>Content to be added in a future session.</div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  ROOT COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function EnergyDashboard() {
  const [activePage, setActivePage] = useState("Overview");

  const renderPage = () => {
    switch (activePage) {
      case "Overview":              return <OverviewPage />;
      case "Appliance Consumption": return <PlaceholderPage title="Appliance Consumption" />;
      case "Comparative Data":      return <PlaceholderPage title="Comparative Data" />;
      case "Data Retrieval":        return <PlaceholderPage title="Data Retrieval" />;
      default:                      return null;
    }
  };

  return (
    <>
      {/* Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #080f18; }
        ::-webkit-scrollbar { width: 6px; } 
        ::-webkit-scrollbar-track { background: #080f18; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
      `}</style>

      <div style={{ minHeight: "100vh", background: "#080f18", display: "flex", flexDirection: "column" }}>

        {/* ── Header ── */}
        <header style={{
          background: "linear-gradient(90deg, #0a1520 0%, #0d1e2e 100%)",
          borderBottom: "1px solid #1e3a5f",
          padding: "18px 28px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#00d4ff", boxShadow: "0 0 10px #00d4ff" }} />
            <span style={{ fontFamily: "'Rajdhani', sans-serif", fontSize: 20, fontWeight: 700, color: "#e8f4f8", letterSpacing: 3, textTransform: "uppercase" }}>
              Home Energy Dashboard
            </span>
          </div>
          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 12, color: "#3a5f7a" }}>
            {new Date().toLocaleString()}
          </span>
        </header>

        {/* ── Tab Bar ── */}
        <TabBar current={activePage} onSelect={setActivePage} />

        {/* ── Page Title Banner ── */}
        <div style={{ background: "#0a1520", padding: "14px 28px", borderBottom: "1px solid #112030" }}>
          <span style={{ fontFamily: "'Rajdhani', sans-serif", fontSize: 13, color: "#3a5f7a", letterSpacing: 2, textTransform: "uppercase" }}>
            {activePage}
          </span>
        </div>

        {/* ── Page Content ── */}
        <main style={{ flex: 1, overflow: "auto" }}>
          {renderPage()}
        </main>
      </div>
    </>
  );
}
