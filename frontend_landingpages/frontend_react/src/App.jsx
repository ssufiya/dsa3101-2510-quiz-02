import { useState } from 'react';
import './App.css';
import { LoginForm } from './pages/loginpage.jsx';
import { Homepage } from './pages/homepage_dashboard.jsx';
import { UploadCSV } from './pages/uploadcsv.jsx';
import { QuestionLibrary } from './pages/question_library.jsx';
import { QuestionDetails } from './pages/question_details.jsx';
import { QuestionCart } from './pages/question_cart.jsx'

export default function App() {
  const [currentScreen, setCurrentScreen] = useState("login"); // "login", "dashboard", "upload"
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [selectedQuestionId, setSelectedQuestionId] = useState(null);



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
  const goToQuestionDetails = (questionId) => {
    setSelectedQuestionId(questionId);  // remember which question was clicked
    setCurrentScreen("questiondetails"); // navigate to details page
  };
  const goToQuestionCart = () => setCurrentScreen("questioncart");


  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  if (currentScreen === "dashboard") {
    return <Homepage onLogout={handleLogout} onGoToUpload={goToUpload} onGoToQuestionLibrary={goToQuestionLibrary} onGoToQuestionCart={goToQuestionCart}/>;
  }

  if (currentScreen === "upload") {
    return <UploadCSV onBack={goToDashboard}/>;
  }

  if (currentScreen === "questionlibrary") {
    return <QuestionLibrary onBack={goToDashboard} onQuestionDetails={goToQuestionDetails}/>;
  }

  if (currentScreen === "questiondetails") {
  return <QuestionDetails
      questionId={selectedQuestionId}   //
      onBack={goToQuestionLibrary}
    />;
  }

  if (currentScreen === "questioncart") {
    return <QuestionCart onBack={goToDashboard} onQuestionCart={goToQuestionCart}/>;
  }

  // fallback
  return null;
}
