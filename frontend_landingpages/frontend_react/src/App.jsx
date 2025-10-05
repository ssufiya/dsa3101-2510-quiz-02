import { useState } from 'react';
import './App.css';
import { LoginForm } from './pages/loginpage.jsx';
import { Homepage } from './pages/homepage_dashboard.jsx';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState("login"); // "login" or "dashboard"
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Function to call when login is successful
  const handleLogin = () => {
    setIsLoggedIn(true);
    setCurrentScreen("dashboard");
  };

  // Function to log out (optional)
  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentScreen("login");
  };

  // Render logic
  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (currentScreen === "dashboard") {
    return <Homepage/>;
  }

  // fallback
  return null;
}

