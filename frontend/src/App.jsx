import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./index.css";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

const initialMatchForm = {
  name: "",
  homeTeam: "",
  awayTeam: "",
  venue: "",
};

const initialRunForm = {
  mode: "offline",
  sourceType: "video",
  sourceUri: "",
};

const runStatuses = ["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELED"];
const matchStatuses = ["PLANNED", "LIVE", "COMPLETED", "ARCHIVED"];

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatTimestamp(value) {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(2)}s`;
}

function statusClass(status) {
  return `status-badge status-${String(status || "unknown").toLowerCase()}`;
}

function App() {
  const [summary, setSummary] = useState(null);
  const [events, setEvents] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [matches, setMatches] = useState([]);
  const [pipelineRuns, setPipelineRuns] = useState([]);
  const [selectedMatchId, setSelectedMatchId] = useState("all");
  const [matchForm, setMatchForm] = useState(initialMatchForm);
  const [runForm, setRunForm] = useState(initialRunForm);
  const [loading, setLoading] = useState(true);
  const [savingMatch, setSavingMatch] = useState(false);
  const [savingRun, setSavingRun] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [
        summaryResponse,
        eventsResponse,
        highlightsResponse,
        matchesResponse,
        runsResponse,
      ] = await Promise.all([
        axios.get(`${API_BASE_URL}/dashboard/summary`),
        axios.get(`${API_BASE_URL}/events`),
        axios.get(`${API_BASE_URL}/highlights/latest`),
        axios.get(`${API_BASE_URL}/matches`),
        axios.get(`${API_BASE_URL}/pipeline-runs`),
      ]);
      setSummary(summaryResponse.data || null);
      setEvents(eventsResponse.data || []);
      setHighlights(highlightsResponse.data || []);
      setMatches(matchesResponse.data || []);
      setPipelineRuns(runsResponse.data || []);
      setError("");
      setLastUpdated(new Date());
    } catch (fetchError) {
      console.error("Failed to fetch dashboard data:", fetchError);
      setError("Dashboard data is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  const selectedMatchIdNumber = selectedMatchId === "all" ? null : Number(selectedMatchId);
  const selectedMatch = useMemo(
    () => matches.find((match) => match.id === selectedMatchIdNumber) || null,
    [matches, selectedMatchIdNumber]
  );

  const visibleRuns = useMemo(() => {
    if (!selectedMatchIdNumber) return pipelineRuns;
    return pipelineRuns.filter((run) => run.matchId === selectedMatchIdNumber);
  }, [pipelineRuns, selectedMatchIdNumber]);

  const activeRunCount = pipelineRuns.filter((run) =>
    ["QUEUED", "RUNNING"].includes(run.status)
  ).length;

  const handleMatchFieldChange = (field, value) => {
    setMatchForm((current) => ({ ...current, [field]: value }));
  };

  const handleRunFieldChange = (field, value) => {
    setRunForm((current) => ({ ...current, [field]: value }));
  };

  const handleCreateMatch = async (event) => {
    event.preventDefault();
    if (!matchForm.name.trim()) return;
    setSavingMatch(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/matches`, {
        ...matchForm,
        sport: "soccer",
      });
      setMatchForm(initialMatchForm);
      setSelectedMatchId(String(response.data.id));
      await fetchDashboardData();
    } catch (createError) {
      console.error("Failed to create match:", createError);
      setError("Could not create match.");
    } finally {
      setSavingMatch(false);
    }
  };

  const handleCreateRun = async (event) => {
    event.preventDefault();
    if (!selectedMatch) return;
    setSavingRun(true);
    try {
      await axios.post(`${API_BASE_URL}/pipeline-runs`, {
        ...runForm,
        matchId: selectedMatch.id,
        status: "QUEUED",
      });
      setRunForm(initialRunForm);
      await fetchDashboardData();
    } catch (createError) {
      console.error("Failed to create pipeline run:", createError);
      setError("Could not create pipeline run.");
    } finally {
      setSavingRun(false);
    }
  };

  const handleMatchStatusChange = async (matchId, status) => {
    try {
      await axios.patch(`${API_BASE_URL}/matches/${matchId}/status`, { status });
      await fetchDashboardData();
    } catch (updateError) {
      console.error("Failed to update match status:", updateError);
      setError("Could not update match status.");
    }
  };

  const handleRunStatusChange = async (runId, status) => {
    try {
      await axios.patch(`${API_BASE_URL}/pipeline-runs/${runId}`, { status });
      await fetchDashboardData();
    } catch (updateError) {
      console.error("Failed to update run status:", updateError);
      setError("Could not update run status.");
    }
  };

  const handleDeleteHighlight = async (highlightId, clipFile) => {
    const confirmed = window.confirm(`Delete "${clipFile}" and its matching timeline event?`);
    if (!confirmed) return;
    try {
      await axios.delete(`${API_BASE_URL}/highlights/${highlightId}/with-event`);
      await fetchDashboardData();
    } catch (deleteError) {
      console.error("Failed to delete highlight and event:", deleteError);
      setError("Could not delete highlight.");
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-title">
          <p className="eyebrow">Live Sports Intelligence</p>
          <h1>Match Operations</h1>
        </div>
        <div className="topbar-actions">
          <span className="live-indicator">
            <span aria-hidden="true" />
            Live feed
          </span>
          <span className="sync-text">Updated {lastUpdated ? formatDate(lastUpdated) : "-"}</span>
          <button className="icon-button" type="button" onClick={fetchDashboardData} title="Refresh">
            <span aria-hidden="true">↻</span>
            Refresh
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>Matches</h2>
            <select
              value={selectedMatchId}
              onChange={(event) => setSelectedMatchId(event.target.value)}
              aria-label="Selected match"
            >
              <option value="all">All matches</option>
              {matches.map((match) => (
                <option key={match.id} value={match.id}>
                  {match.name}
                </option>
              ))}
            </select>
          </div>

          <div className="match-list">
            {matches.length === 0 ? (
              <div className="empty-state">No matches yet.</div>
            ) : (
              matches.map((match) => (
                <button
                  key={match.id}
                  className={`match-row ${selectedMatchIdNumber === match.id ? "active" : ""}`}
                  type="button"
                  onClick={() => setSelectedMatchId(String(match.id))}
                >
                  <span>
                    <strong>{match.name}</strong>
                    <small>{match.homeTeam || "Home"} vs {match.awayTeam || "Away"}</small>
                  </span>
                  <span className={statusClass(match.status)}>{match.status}</span>
                </button>
              ))
            )}
          </div>

          <form className="compact-form" onSubmit={handleCreateMatch}>
            <h3>New Match</h3>
            <label>
              Name
              <input
                value={matchForm.name}
                onChange={(event) => handleMatchFieldChange("name", event.target.value)}
                placeholder="Championship Final"
              />
            </label>
            <div className="form-grid">
              <label>
                Home
                <input
                  value={matchForm.homeTeam}
                  onChange={(event) => handleMatchFieldChange("homeTeam", event.target.value)}
                  placeholder="Home"
                />
              </label>
              <label>
                Away
                <input
                  value={matchForm.awayTeam}
                  onChange={(event) => handleMatchFieldChange("awayTeam", event.target.value)}
                  placeholder="Away"
                />
              </label>
            </div>
            <label>
              Venue
              <input
                value={matchForm.venue}
                onChange={(event) => handleMatchFieldChange("venue", event.target.value)}
                placeholder="Stadium"
              />
            </label>
            <button className="primary-button" type="submit" disabled={savingMatch || !matchForm.name.trim()}>
              <span aria-hidden="true">+</span>
              {savingMatch ? "Creating" : "Create Match"}
            </button>
          </form>
        </aside>

        <main className="main">
          <section className="match-strip">
            <div>
              <p className="section-kicker">Selected</p>
              <h2>{selectedMatch ? selectedMatch.name : "All matches"}</h2>
              <p>{selectedMatch ? `${selectedMatch.homeTeam || "Home"} vs ${selectedMatch.awayTeam || "Away"}` : "Global event and highlight feed"}</p>
            </div>
            {selectedMatch && (
              <select
                value={selectedMatch.status}
                onChange={(event) => handleMatchStatusChange(selectedMatch.id, event.target.value)}
                aria-label="Match status"
              >
                {matchStatuses.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            )}
          </section>

          <section className="metric-grid" aria-label="Dashboard summary">
            <div className="metric">
              <span>Latest Score</span>
              <strong>{summary?.latestScore || "-"}</strong>
            </div>
            <div className="metric">
              <span>Latest Clock</span>
              <strong>{summary?.latestClock || "-"}</strong>
            </div>
            <div className="metric">
              <span>Events</span>
              <strong>{summary?.totalEvents ?? events.length}</strong>
            </div>
            <div className="metric">
              <span>Highlights</span>
              <strong>{summary?.totalHighlights ?? highlights.length}</strong>
            </div>
            <div className="metric">
              <span>Active Runs</span>
              <strong>{activeRunCount}</strong>
            </div>
          </section>

          <section className="content-grid">
            <div className="panel run-panel">
              <div className="panel-header">
                <div>
                  <p className="section-kicker">Pipeline</p>
                  <h2>Runs</h2>
                </div>
                <span className="count-pill">{visibleRuns.length}</span>
              </div>

              <form className="run-form" onSubmit={handleCreateRun}>
                <select
                  value={runForm.mode}
                  onChange={(event) => handleRunFieldChange("mode", event.target.value)}
                  aria-label="Run mode"
                  disabled={!selectedMatch}
                >
                  <option value="offline">Offline</option>
                  <option value="live">Live</option>
                </select>
                <input
                  value={runForm.sourceUri}
                  onChange={(event) => handleRunFieldChange("sourceUri", event.target.value)}
                  placeholder="Source URI"
                  disabled={!selectedMatch}
                />
                <button className="secondary-button" type="submit" disabled={!selectedMatch || savingRun}>
                  <span aria-hidden="true">+</span>
                  {savingRun ? "Queuing" : "Queue Run"}
                </button>
              </form>

              {visibleRuns.length === 0 ? (
                <div className="empty-state">No pipeline runs found.</div>
              ) : (
                <div className="run-list">
                  {visibleRuns.map((run) => (
                    <div className="run-row" key={run.id}>
                      <div>
                        <strong>{run.mode}</strong>
                        <small>{run.matchName || "Unassigned"} · {run.sourceType || "source"}</small>
                      </div>
                      <div className="run-metrics">
                        <span>{run.framesProcessed || 0} frames</span>
                        <span>{run.eventsDetected || 0} events</span>
                        <span>{run.highlightsGenerated || 0} clips</span>
                      </div>
                      <select
                        value={run.status}
                        onChange={(event) => handleRunStatusChange(run.id, event.target.value)}
                        aria-label={`Run ${run.id} status`}
                      >
                        {runStatuses.map((status) => (
                          <option key={status} value={status}>{status}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="panel timeline-panel">
              <div className="panel-header">
                <div>
                  <p className="section-kicker">Timeline</p>
                  <h2>Score Events</h2>
                </div>
                <span className="count-pill">{events.length}</span>
              </div>
              {loading ? (
                <div className="empty-state">Loading dashboard...</div>
              ) : events.length === 0 ? (
                <div className="empty-state">No score events found.</div>
              ) : (
                <div className="timeline-list">
                  {events.map((event) => (
                    <div className="timeline-row" key={event.id}>
                      <span className="time-chip">{event.clock}</span>
                      <div>
                        <strong>{event.oldScore} -&gt; {event.newScore}</strong>
                        <small>{formatTimestamp(event.videoTimestamp)} · {event.file}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="panel highlights-panel">
            <div className="panel-header">
              <div>
                <p className="section-kicker">Review</p>
                <h2>Recent Highlights</h2>
              </div>
              <span className="count-pill">{highlights.length}</span>
            </div>

            {highlights.length === 0 ? (
              <div className="empty-state">No highlights found.</div>
            ) : (
              <div className="highlight-grid">
                {highlights.map((highlight) => (
                  <article className="highlight-card" key={highlight.id}>
                    <video controls className="video-player">
                      <source
                        src={`${API_BASE_URL}/highlights/file/${encodeURIComponent(highlight.clipFile)}`}
                        type="video/mp4"
                      />
                      Your browser does not support the video tag.
                    </video>
                    <div className="highlight-body">
                      <div>
                        <span className="time-chip">{highlight.clock}</span>
                        <h3>{highlight.oldScore} -&gt; {highlight.newScore}</h3>
                        <p>{highlight.clipFile}</p>
                      </div>
                      <dl>
                        <div>
                          <dt>Start</dt>
                          <dd>{formatTimestamp(highlight.clipStartTime)}</dd>
                        </div>
                        <div>
                          <dt>Duration</dt>
                          <dd>{formatTimestamp(highlight.duration)}</dd>
                        </div>
                      </dl>
                      <button
                        className="danger-button"
                        type="button"
                        onClick={() => handleDeleteHighlight(highlight.id, highlight.clipFile)}
                      >
                        <span aria-hidden="true">x</span>
                        Delete
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
