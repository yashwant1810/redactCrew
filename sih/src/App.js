import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./Home";
import PiiRedaction from "./piiRedaction";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pii-redaction" element={<PiiRedaction />} />
      </Routes>
    </Router>
  );
}

export default App;