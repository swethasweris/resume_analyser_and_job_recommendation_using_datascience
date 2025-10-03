import React, { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [hrFiles, setHrFiles] = useState([]);
const [hrJobRole, setHrJobRole] = useState("");
const [bestResume, setBestResume] = useState(null); // new state for HR result


  // Upload resume & analyze
  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      setError("Please choose a resume file");
      return;
    }

    const form = new FormData();
    form.append("file", file);
    setLoading(true);

    try {
      const res = await fetch("/api/analyze", { method: "POST", body: form });
      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Save chosen learning path
  const handleChoose = async (learningPath) => {
    if (!user) {
      // Redirect to login/signup if not logged in
      window.location.href = "/signup";
      return;
    }

    try {
      const res = await fetch("/api/choose-path", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ userId: user.id, path: learningPath }),
      });

      if (!res.ok) throw new Error("Failed to save learning path");
      alert("✅ Learning path saved to your dashboard!");
    } catch (err) {
      alert("❌ " + err.message);
    }
  };

  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, Arial",
        maxWidth: 980,
        margin: "24px auto",
        padding: 16,
      }}
    >
      <h1>🚀 IT Career Recommender</h1>
      <p>
        Upload your resume (PDF/DOCX). We’ll extract skills and recommend
        matching roles, skill gaps, and a learning path.
      </p>

      {/* Resume Upload Form */}
      <form
        onSubmit={onSubmit}
        style={{ display: "flex", gap: 12, alignItems: "center" }}
      >
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0])}
        />
        <button
          disabled={loading}
          type="submit"
          style={{
            background: "#007bff",
            color: "#fff",
            border: "none",
            padding: "8px 16px",
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {/* Error */}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {/* Results */}
      {result && (
        <div style={{ marginTop: 24 }}>
          {/* Extracted Text */}
          <section>
            <h2>📌 Extracted Info</h2>
            <pre
              style={{
                background: "#111",
                color: "#eee",
                padding: 12,
                borderRadius: 8,
                overflowX: "auto",
              }}
            >
              {JSON.stringify(result.extracted, null, 2)}
            </pre>
          </section>

          {/* Recommendations */}
          <section>
            <h2>🎯 Top Recommendations</h2>
            {result.recommendations.map((r, i) => (
              <div
                key={i}
                style={{
                  border: "1px solid #ccc",
                  padding: 16,
                  borderRadius: 10,
                  marginBottom: 16,
                  background: "#f9f9f9",
                }}
              >
                <h3>
                  {r.role} —{" "}
                  <span style={{ color: "green" }}>
                    Score: {r.score.toFixed(3)}
                  </span>
                </h3>
                <p>
                  <strong>✅ Matched:</strong>{" "}
                  {r.matched_skills.join(", ") || "—"}
                </p>
                <p>
                  <strong>❌ Missing:</strong>{" "}
                  {r.missing_skills.join(", ") || "—"}
                </p>

                {/* Learning Path */}
                <div style={{ marginTop: 12 }}>
                  <h4>📚 Learning Path (Flow)</h4>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                      flexWrap: "wrap",
                    }}
                  >
                    {r.learning_plan.map((lp, idx) => (
                      <React.Fragment key={idx}>
                        <div
                          style={{
                            border: "2px solid #007bff",
                            borderRadius: 12,
                            padding: "12px 16px",
                            background: "#eef6ff",
                            minWidth: 160,
                            textAlign: "center",
                          }}
                        >
                          <strong>{lp.skill}</strong>
                          <ul style={{ textAlign: "left", paddingLeft: 18 }}>
                            {lp.steps.map((s, k) => (
                              <li key={k}>{s}</li>
                            ))}
                          </ul>
                          <div style={{ fontSize: "0.9em", marginTop: 6 }}>
                            <em>Project:</em> {lp.project_idea}
                          </div>
                          <div style={{ fontSize: "0.8em", color: "#555" }}>
                            ⏱ {lp.estimated_hours} hrs
                          </div>
                        </div>
                        {idx < r.learning_plan.length - 1 && (
                          <div
                            style={{
                              fontSize: "1.5em",
                              color: "#007bff",
                            }}
                          >
                            ➡️
                          </div>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                {/* Choose Button */}
                <button
                  onClick={() => handleChoose(r.learning_plan)}
                  style={{
                    marginTop: 16,
                    background: "#28a745",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  Choose This Path
                </button>
              </div>
            ))}
          </section>

          {/* Career Roadmap */}
          <section>
            <h2>🛤 Career Roadmap</h2>
            <ol>
              {result.roadmap.map((s, idx) => (
                <li key={idx}>
                  <strong>{s.role}</strong>: {s.focus}
                </li>
              ))}
            </ol>
          </section>
        </div>
      )}
      {/* ---------------- HR Section ---------------- */}
<section style={{ marginTop: 48 }}>
  <h2>HR: Upload Multiple Resumes for a Job Role</h2>
  <form
    onSubmit={async (e) => {
      e.preventDefault();
      setError(null);
      setBestResume(null);

      if (!hrFiles || hrFiles.length === 0) {
        setError("Please upload at least one resume");
        return;
      }
      if (!hrJobRole) {
        setError("Please enter the job role");
        return;
      }

      const form = new FormData();
      hrFiles.forEach((f) => form.append("files", f));
      form.append("job_role", hrJobRole);

      setLoading(true);
      try {
        const res = await fetch("/api/hr/analyze-best", {
          method: "POST",
          body: form,
        });
        if (!res.ok) throw new Error("HR analysis failed");
        const data = await res.json();
        setBestResume(data.best_resume);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }}
    style={{ display: "flex", flexDirection: "column", gap: 12 }}
  >
    <input
      type="text"
      placeholder="Enter Job Role"
      value={hrJobRole}
      onChange={(e) => setHrJobRole(e.target.value)}
    />
    <input
      type="file"
      accept=".pdf,.docx,.txt"
      multiple
      onChange={(e) => setHrFiles(Array.from(e.target.files))}
    />
    <button
      type="submit"
      disabled={loading}
      style={{
        background: "#6f42c1",
        color: "#fff",
        border: "none",
        padding: "8px 16px",
        borderRadius: 6,
        cursor: "pointer",
      }}
    >
      {loading ? "Processing..." : "Find Best Resume"}
    </button>
  </form>

  {bestResume && (
    <div
      style={{
        marginTop: 16,
        padding: 16,
        border: "1px solid #ccc",
        borderRadius: 8,
        background: "#f0f8ff",
      }}
    >
      <h3>🏆 Best Resume for "{hrJobRole}"</h3>
      <p>
        <strong>File:</strong> {bestResume.filename}
      </p>
      <p>
        <strong>Score:</strong> {bestResume.score.toFixed(3)}
      </p>
      <p>
        <strong>Matched Skills:</strong> {bestResume.matched_skills.join(", ")}
      </p>
      <p>
        <strong>Missing Skills:</strong> {bestResume.missing_skills.join(", ")}
      </p>
    </div>
  )}
</section>

    </div>
    
  );
}
