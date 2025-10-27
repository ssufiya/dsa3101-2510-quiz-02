import { useState } from "react";
import "./App.css";
import { LoginForm } from "./pages/loginpage.jsx";
import { Homepage } from "./pages/homepage_dashboard.jsx";
import { UploadCSV } from "./pages/uploadcsv.jsx";
import { QuestionLibrary } from "./pages/question_library.jsx";
import { QuestionDetails } from "./pages/question_details.jsx";
import { QuestionCart } from "./pages/question_cart.jsx";
import EditQuestion from "./pages/edit_question.jsx";

export default function App() {
  const [currentScreen, setCurrentScreen] = useState("login");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [selectedQuestionId, setSelectedQuestionId] = useState(null);
  const [cartQuestions, setCartQuestions] = useState([]);
  const [questionLibraryData, setQuestionLibraryData] = useState([]);

  // 👇 track where the cart was opened from
  const [fromDetailsPage, setFromDetailsPage] = useState(false);

  // ---------- Navigation Handlers ----------
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
    setSelectedQuestionId(questionId);
    setCurrentScreen("questiondetails");
  };

  // When navigating to cart, track where user came from
  const goToQuestionCart = (fromDetails = false) => {
    setFromDetailsPage(fromDetails);
    setCurrentScreen("questioncart");
  };

  const goToEditQuestion = (questionId) => {
    setSelectedQuestionId(questionId);
    setCurrentScreen("editquestion");
  };

  // ---------- Cart Handlers ----------
  const addToCart = (question) => {
    if (!cartQuestions.find((q) => q.question_id === question.question_id)) {
      setCartQuestions((prev) => [...prev, question]);
    }
  };

  const removeFromCart = (questionId) => {
    setCartQuestions((prev) => prev.filter((q) => q.question_id !== questionId));
  };

  // ---------- Update question after edit ----------
  const handleSaveQuestion = (updatedQuestion) => {
    setQuestionLibraryData((prev) =>
      prev.map((q) => (q.id === updatedQuestion.id ? updatedQuestion : q))
    );
  };

  // ---------- Render Screens ----------
  if (!isLoggedIn) return <LoginForm onLogin={handleLogin} />;

  if (currentScreen === "dashboard") {
    return (
      <Homepage
        onLogout={handleLogout}
        onGoToUpload={goToUpload}
        onGoToQuestionLibrary={goToQuestionLibrary}
        onGoToQuestionCart={() => goToQuestionCart(false)} // from dashboard
      />
    );
  }

  if (currentScreen === "upload") {
    return <UploadCSV onBack={goToDashboard} />;
  }

  if (currentScreen === "questionlibrary") {
    return (
      <QuestionLibrary
        onBack={goToDashboard}
        onQuestionDetails={goToQuestionDetails}
        questionData={questionLibraryData}
        onGoToQuestionCart={() => goToQuestionCart(false)} // from library
        onAddToCart={addToCart}
        cartQuestions={cartQuestions}
      />
    );
  }

  if (currentScreen === "questiondetails") {
    const question = questionLibraryData.find((q) => q.id === selectedQuestionId);
    return (
      <QuestionDetails
        questionId={selectedQuestionId}
        questionData={question}
        onBack={goToQuestionLibrary}
        onEditQuestion={goToEditQuestion}
        onViewQuestion={goToQuestionDetails}
        onGoToQuestionCart={() => goToQuestionCart(true)} // ✅ from details page
        onAddToCart={addToCart}
        cartQuestions={cartQuestions}
      />
    );
  }

  if (currentScreen === "editquestion") {
    const question = questionLibraryData.find((q) => q.id === selectedQuestionId);
    return (
      <EditQuestion
        questionId={selectedQuestionId}
        questionData={question}
        onBack={() => goToQuestionDetails(selectedQuestionId)}
        onSave={handleSaveQuestion}
      />
    );
  }

  if (currentScreen === "questioncart") {
    return (
      <QuestionCart
        onBack={goToDashboard}
        onBackToLibrary={goToQuestionLibrary}
        onBackToDetails={goToQuestionDetails}
        selectedQuestionId={selectedQuestionId}
        questions={cartQuestions}
        onRemoveQuestion={removeFromCart}
        fromDetailsPage={fromDetailsPage} // ✅ pass flag here
      />
    );
  }

  return null;
}
