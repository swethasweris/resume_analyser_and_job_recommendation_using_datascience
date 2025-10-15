import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [hrFiles, setHrFiles] = useState([]);
  const [hrJobRole, setHrJobRole] = useState("");
  const [bestResume, setBestResume] = useState(null);

  // Upload resume & analyze (for candidate)
  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!file) {
      setError("⚠️ Please choose a resume file.");
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

  // HR Analysis Handler
  const handleHrSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setBestResume(null);

    if (!hrFiles || hrFiles.length === 0) {
      setError("⚠️ Please upload at least one resume.");
      return;
    }
    if (!hrJobRole) {
      setError("⚠️ Please enter the job role.");
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
  };

  return (
    <div
      className="container my-5"
      style={{
        fontFamily: "Inter, system-ui, Arial",
        maxWidth: "950px",
      }}
    >
      <div className="text-center mb-4">
        <h1 className="fw-bold text-primary">🚀 IT Career Recommender</h1>
        <p className="text-secondary">
          Upload your resume (PDF/DOCX). We'll extract skills, suggest matching
          roles, detect gaps, and generate a personalized learning path.
        </p>
      </div>

      {/* Resume Upload Form */}
      <form
        onSubmit={onSubmit}
        className="d-flex flex-wrap gap-3 justify-content-center align-items-center mb-3"
      >
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          className="form-control w-auto"
          onChange={(e) => setFile(e.target.files?.[0])}
        />
        <button
          disabled={loading}
          type="submit"
          className="btn btn-primary px-4"
        >
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
      </form>

      {/* Error Message */}
      {error && <p className="text-danger fw-semibold">{error}</p>}

      {/* Candidate Results */}
      {result && (
        <div className="mt-4">
          {/* Extracted Info */}
          <section className="mb-4">
            <h4>📌 Extracted Info</h4>
            <pre
              style={{
                background: "#1e1e1e",
                color: "#fff",
                padding: "15px",
                borderRadius: "8px",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(result.extracted, null, 2)}
            </pre>
          </section>

          {/* Recommendations */}
          <section className="mb-4">
            <h4>🎯 Top Recommendations</h4>
            {result.recommendations.map((r, i) => (
              <div
                key={i}
                className="card shadow-sm mb-4 border-0"
                style={{ borderRadius: "12px" }}
              >
                <div className="card-body">
                  <h5 className="card-title text-dark fw-bold">
                    {r.role}{" "}
                    <span className="text-success">
                      — Score: {r.score.toFixed(3)}
                    </span>
                  </h5>
                  <p className="mb-1">
                    <strong>✅ Matched:</strong>{" "}
                    {r.matched_skills.join(", ") || "—"}
                  </p>
                  <p>
                    <strong>❌ Missing:</strong>{" "}
                    {r.missing_skills.join(", ") || "—"}
                  </p>

                  {/* Learning Path */}
                  <div>
                    <h6 className="fw-bold mt-3 mb-2">📚 Learning Path</h6>
                    <div className="d-flex flex-wrap align-items-start gap-3">
                      {r.learning_plan.map((lp, idx) => (
                        <React.Fragment key={idx}>
                          <div
                            className="p-3 border border-primary rounded bg-light"
                            style={{ minWidth: "200px" }}
                          >
                            <h6 className="text-primary text-center">
                              {lp.skill}
                            </h6>
                            <ul style={{ fontSize: "0.9em" }}>
                              {lp.steps.map((s, k) => (
                                <li key={k}>{s}</li>
                              ))}
                            </ul>
                            <small className="text-muted">
                              ⏱ {lp.estimated_hours} hrs
                            </small>
                            <div className="mt-2 fst-italic">
                              Project: {lp.project_idea}
                            </div>
                          </div>
                          {idx < r.learning_plan.length - 1 && (
                            <div
                              style={{
                                fontSize: "1.4em",
                                color: "#007bff",
                                alignSelf: "center",
                              }}
                            >
                              ➡️
                            </div>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => handleChoose(r.learning_plan)}
                    className="btn btn-success mt-3"
                  >
                    Choose This Path
                  </button>
                </div>
              </div>
            ))}
          </section>

          {/* Career Roadmap */}
          
        </div>
      )}

      {/* HR Section */}
      <section className="mt-5 p-4 bg-light rounded shadow-sm">
        <h4 className="text-center text-dark fw-bold mb-3">
          👩‍💼 HR Panel: Upload Multiple Resumes
        </h4>
        <form
          onSubmit={handleHrSubmit}
          className="d-flex flex-column gap-3 align-items-center"
        >
          <input
            type="text"
            className="form-control w-50"
            placeholder="Enter Job Role (e.g., Data Scientist)"
            value={hrJobRole}
            onChange={(e) => setHrJobRole(e.target.value)}
          />
          <input
            type="file"
            className="form-control w-50"
            accept=".pdf,.docx,.txt"
            multiple
            onChange={(e) => setHrFiles(Array.from(e.target.files))}
          />
          <button
            type="submit"
            disabled={loading}
            className="btn btn-purple px-4"
            style={{
              backgroundColor: "#6f42c1",
              color: "#fff",
              borderRadius: "6px",
            }}
          >
            {loading ? "Processing..." : "Find Best Resume"}
          </button>
        </form>

        {bestResume && (
          <div className="mt-4 p-4 border rounded bg-white shadow-sm">
            <h5 className="text-success">
              🏆 Best Resume for "{hrJobRole}"
            </h5>
            <p>
              <strong>File:</strong> {bestResume.filename}
            </p>
            <p>
              <strong>Score:</strong> {bestResume.score.toFixed(3)}
            </p>
            <p>
              <strong>Matched Skills:</strong>{" "}
              {bestResume.matched_skills.join(", ")}
            </p>
            <p>
              <strong>Missing Skills:</strong>{" "}
              {bestResume.missing_skills.join(", ")}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
