import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import QRAssistantPage from "./components/QRAssistantPage";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<QRAssistantPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;