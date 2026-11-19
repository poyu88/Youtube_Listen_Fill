import { Navigate, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Practice from "./pages/Practice";

/**
 * 應用路由根元件。
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/practice/:videoId" element={<Practice />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
