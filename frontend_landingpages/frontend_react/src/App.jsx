import { useState } from 'react';
import './App.css';
import { LoginForm } from './pages/loginpage.jsx';
import { Homepage } from './pages/homepage_dashboard.jsx';
import { UploadCSV } from './pages/uploadcsv.jsx';
import { QuestionLibrary } from './pages/question_library.jsx';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState("login"); // "login", "dashboard", "upload"
  const [isLoggedIn, setIsLoggedIn] = useState(false);


  const handleLogin = () => {
    setIsLoggedIn(true);
    setCurrentScreen("dashboard");
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentScreen("login");
  };

  const goToUpload = () => setCurrentScreen("upload");
  const goToDashboard = () => setCurrentScreen("dashboard");
  const goToQuestionLibrary = () => setCurrentScreen("questionlibrary");

  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (currentScreen === "dashboard") {
    return <Homepage onLogout={handleLogout} onGoToUpload={goToUpload} onGoToQuestionLibrary={goToQuestionLibrary} />;
  }

  if (currentScreen === "upload") {
    return <UploadCSV onBack={goToDashboard}/>;
  }

  if (currentScreen === "questionlibrary") {
    return <QuestionLibrary onBack={goToDashboard}/>
  }

  // fallback
  return null;
}
