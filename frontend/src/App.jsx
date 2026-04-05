import { useEffect, useState } from "react";
import axios from "axios";
import "./index.css";

const API_BASE_URL = "http://localhost:8080/api";

function App() {
  const [events, setEvents] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [eventsResponse, highlightsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/events/latest`),
        axios.get(`${API_BASE_URL}/highlights/latest`),
      ]);

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

  return (
    <div className="app">
      <header className="header">
        <h1>Live Sports Intelligence</h1>
        <p>Real-time score event detection and AI highlight generation</p>
      </header>

      {loading ? (
        <p className="loading">Loading dashboard...</p>
      ) : (
        <div className="dashboard-grid">
          <section className="card">
            <h2>Recent Score Events</h2>
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

                    <video
                      controls
                      width="100%"
                      className="video-player"
                    >
                      <source src={`file://${highlight.clipPath}`} type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default App;