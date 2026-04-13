import { useEffect, useState } from "react";
import axios from "axios";
import "./index.css";

const API_BASE_URL = "http://localhost:8080/api";

function App() {
  const [summary, setSummary] = useState(null);
  const [events, setEvents] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetchDashboardData = async () => {
    try {
      const [summaryResponse, eventsResponse, highlightsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/dashboard/summary`),
        axios.get(`${API_BASE_URL}/events`),
        axios.get(`${API_BASE_URL}/highlights/latest`),
      ]);
      setSummary(summaryResponse.data || null);
      setEvents(eventsResponse.data || []);
      setHighlights(highlightsResponse.data || []);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  const handleDeleteHighlight = async (highlightId, clipFile) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${clipFile}" and its matching timeline event?`
    );
    if (!confirmed) return;
    try {
      await axios.delete(`${API_BASE_URL}/highlights/${highlightId}/with-event`);
      await fetchDashboardData();
    } catch (error) {
      console.error("Failed to delete highlight and event:", error);
      alert("Failed to delete highlight.");
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Live Sports Intelligence</h1>
        <p>Real-time score event detection and highlight generation dashboard</p>
      </header>
      {loading ? (
        <p className="loading">Loading dashboard...</p>
      ) : (
        <>
          {summary && (
            <section className="summary-grid">
              <div className="summary-card">
                <h3>Latest Clock</h3>
                <p>{summary.latestClock}</p>
              </div>
              <div className="summary-card">
                <h3>Latest Score</h3>
                <p>{summary.latestScore}</p>
              </div>
              <div className="summary-card">
                <h3>Latest Event</h3>
                <p>{summary.latestEvent}</p>
              </div>
              <div className="summary-card">
                <h3>Total Highlights</h3>
                <p>{summary.totalHighlights}</p>
              </div>
            </section>
          )}
          <div className="dashboard-grid">
            <section className="card">
              <h2>Match Timeline</h2>
              {events.length === 0 ? (
                <p>No score events found.</p>
              ) : (
                <div className="list">
                  {events.map((event) => (
                    <div className="list-item" key={event.id}>
                      <p><strong>Clock:</strong> {event.clock}</p>
                      <p><strong>Score Change:</strong> {event.oldScore} → {event.newScore}</p>
                      <p><strong>Video Timestamp:</strong> {event.videoTimestamp}s</p>
                      <p><strong>File:</strong> {event.file}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
            <section className="card">
              <h2>Recent Highlights</h2>
              {highlights.length === 0 ? (
                <p>No highlights found.</p>
              ) : (
                <div className="list">
                  {highlights.map((highlight) => (
                    <div className="list-item" key={highlight.id}>
                      <p><strong>Clock:</strong> {highlight.clock}</p>
                      <p><strong>Score Change:</strong> {highlight.oldScore} → {highlight.newScore}</p>
                      <p><strong>Clip:</strong> {highlight.clipFile}</p>
                      <p><strong>Start:</strong> {highlight.clipStartTime}s</p>
                      <p><strong>Duration:</strong> {highlight.duration}s</p>

                      <video controls width="100%" className="video-player">
                        <source
                          src={`http://localhost:8080/api/highlights/file/${highlight.clipFile}`}
                          type="video/mp4"
                        />
                        Your browser does not support the video tag.
                      </video>
                      <button
                        className="delete-button"
                        onClick={() => handleDeleteHighlight(highlight.id, highlight.clipFile)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
export default App;