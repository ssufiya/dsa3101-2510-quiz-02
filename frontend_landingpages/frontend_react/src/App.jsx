import { useState } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LoginForm } from './pages/loginpage.jsx';
import { Homepage } from './pages/homepage_dashboard.jsx';
import { UploadQuestions } from './pages/uploadcsv.jsx';


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
  /* if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (currentScreen === "dashboard") {
    return <Homepage/>;
  }
 */
  // test upload csv page

  return (
    <Router>
      <Routes>
        {/* 👇 This special route lets you test UploadQuestions directly */}
        <Route path="/uploadcsv" element={<UploadQuestions onBack={() => window.history.back()} />} />

        {/* 👇 Everything else uses your existing screen logic */}
        <Route
          path="*"
          element={
            !isLoggedIn ? (
              <LoginForm onLogin={handleLogin} />
            ) : currentScreen === "dashboard" ? (
              <Homepage />
            ) : null
          }
        />
      </Routes>
    </Router>
  );
}

