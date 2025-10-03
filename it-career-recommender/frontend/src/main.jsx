// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import Root from "./Root";   // ✅ not App


ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
