import { useState, useEffect } from "react";
import App from "./App.jsx";
import VotingManagement from "./components/VotingManagement.jsx";

export default function AppRouter() {
  const [currentRoute, setCurrentRoute] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentRoute(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Management page
  if (currentRoute === "/management" || currentRoute === "/management/") {
    return <VotingManagement />;
  }

  // Main donation display
  return <App />;
}

