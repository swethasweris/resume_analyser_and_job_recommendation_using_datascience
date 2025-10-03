import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";


export default function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        
      </Routes>
    </BrowserRouter>
  );
}
