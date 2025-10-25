import { useState, useEffect } from "react";
import axios from "axios";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { ArrowLeft, HelpCircle, Eye, Plus, ShoppingBasket, Edit, ChevronDown, ChevronUp } from "lucide-react";
import EditQuestion from "./edit_question.jsx";

export function QuestionDetails({
  questionId,
  onBack = () => {},
  onViewQuestion,
  onGoToQuestionCart,
  onAddToCart,
  cartQuestions = [],
}) {
  const [questionData, setQuestionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(true);
  const [changeHistory, setChangeHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedIndices, setExpandedIndices] = useState([]);
  const [isEditing, setIsEditing] = useState(false);

  // Fetch question details
  useEffect(() => {
    const fetchQuestionData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`http://localhost:5003/api/questions/${questionId}`);
        setQuestionData(response.data.data);
      } catch (error) {
        console.error("Error fetching question:", error);
      } finally {
        setLoading(false);
      }
    };
    if (questionId) fetchQuestionData();
  }, [questionId]);

  // Fetch similar questions
  useEffect(() => {
    const fetchSimilarQuestions = async () => {
      try {
        setLoadingSimilar(true);
        const suggestionsRes = await axios.get(
          `http://localhost:5003/api/questions/${questionId}/suggestions?top_n=5`
        );
        const suggestedVariants = suggestionsRes.data.suggested_variants || [];

        const detailsPromises = suggestedVariants.map((s) =>
          axios
            .get(`http://localhost:5003/api/questions/${s.question_id}`)
            .then((res) => ({
              ...res.data.data,
              similarity: s.similarity,
            }))
        );

        const details = await Promise.all(detailsPromises);
        setSimilarQuestions(details);
      } catch (err) {
        console.error("Error fetching similar questions:", err);
      } finally {
        setLoadingSimilar(false);
      }
    };
    if (questionId) fetchSimilarQuestions();
  }, [questionId]);

  // Fetch change history
  useEffect(() => {
    const fetchChangeHistory = async () => {
      try {
        setLoadingHistory(true);
        const changeRes = await axios.get(
          `http://localhost:5003/api/questions/${questionId}/change-history`
        );
        setChangeHistory(changeRes.data.changes || []);
      } catch (err) {
        console.error("Error fetching change history:", err);
      } finally {
        setLoadingHistory(false);
      }
    };
    if (questionId) fetchChangeHistory();
  }, [questionId]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case "low":
      case "easy":
        return "bg-green-100 text-green-800";
      case "med":
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDateTime = (dateStr) => {
    try {
      const date = new Date(dateStr);
      const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      return date.toLocaleString("en-GB", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
        timeZoneName: "short",
        timeZone: userTimeZone,
      });
    } catch {
      return dateStr;
    }
  };

  const timeAgo = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} day${days !== 1 ? "s" : ""} ago`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} month${months !== 1 ? "s" : ""} ago`;
    const years = Math.floor(months / 12);
    return `${years} year${years !== 1 ? "s" : ""} ago`;
  };

  const toggleExpand = (idx) => {
    setExpandedIndices((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

  const handleAddToCart = (question) => {
    if (!isInCart(question.question_id) && onAddToCart) onAddToCart(question);
  };

  const handleViewDetails = (id) => {
    if (onViewQuestion) {
      onViewQuestion(id);
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
      setLoading(true);
      axios
        .get(`http://localhost:5003/api/questions/${id}`)
        .then((res) => setQuestionData(res.data.data))
        .finally(() => setLoading(false));
    }
  };

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading question details...
      </div>
    );

  if (!questionData)
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Question not found.
      </div>
    );

  if (isEditing)
    return (
      <EditQuestion
        questionId={questionId}
        questionData={questionData}
        onBack={() => setIsEditing(false)}
        onSave={(updated) => setQuestionData(updated)}
      />
    );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={onBack}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Library</span>
              </Button>
              <div className="flex items-center space-x-3">
                <div className="bg-primary rounded-lg p-2">
                  <HelpCircle className="h-6 w-6 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold">Question Details</h1>
                  <p className="text-sm text-muted-foreground">
                    {questionData.course_code} – {questionData.course_name}
                  </p>
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              onClick={onGoToQuestionCart}
              className="flex items-center space-x-2"
            >
              <ShoppingBasket className="h-5 w-5" />
              <span>Cart ({cartQuestions.length})</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="flex-1 space-y-6">
            {/* Question Card */}
            <Card>
              <CardHeader className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <Badge className={getDifficultyColor(questionData.difficulty)}>
                    {questionData.difficulty}
                  </Badge>
                  <span className="font-semibold">{questionData.assessment_type}</span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsEditing(true)}
                  className="flex items-center space-x-1"
                >
                  <Edit className="h-4 w-4" />
                  <span>Edit</span>
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-gray-800 text-base font-medium">{questionData.question_text}</div>

                {questionData.options && (
                  <ul className="mt-2 space-y-1">
                    {Object.entries(questionData.options).map(([key, value]) => (
                      <li key={key} className="flex items-center space-x-2">
                        <span className="font-semibold">{key}.</span>
                        <span>{value}</span>
                        {questionData.correct_answer === key && (
                          <span className="text-green-600 ml-2">✅</span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}

                {questionData.explanation && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-900 whitespace-pre-line">
                    <strong>Explanation:</strong> {questionData.explanation}
                  </div>
                )}

                {questionData.concepts && questionData.concepts.length > 0 && (
                  <p className="text-sm text-gray-700 mt-3">
                    <strong>Concepts:</strong> {questionData.concepts.join(", ")}
                  </p>
                )}
              </CardContent>

              <div className="p-4 border-t border-gray-200 flex justify-end">
                <Button
                  size="sm"
                  onClick={() => handleAddToCart(questionData)}
                  disabled={isInCart(questionData.question_id)}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  {isInCart(questionData.question_id) ? "Added to Cart" : "Add to Cart"}
                </Button>
              </div>
            </Card>

            {/* Change History */}
            <Card>
              <CardHeader>
                <CardTitle>Change History</CardTitle>
                <CardDescription>
                  (Timestamps shown in your local timezone)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loadingHistory ? (
                  <p className="text-sm text-gray-500 mt-2">Loading change history...</p>
                ) : changeHistory.length === 0 ? (
                  <p className="text-sm text-gray-500 mt-2">No change history available.</p>
                ) : (
                  <ul className="space-y-4 mt-2">
                    {changeHistory.map((c, idx) => {
                      const expanded = expandedIndices.includes(idx);
                      return (
                        <li
                          key={idx}
                          className="p-3 border border-gray-200 rounded bg-gray-50 space-y-1"
                        >
                          <div
                            className="flex justify-between items-center cursor-pointer"
                            onClick={() => toggleExpand(idx)}
                          >
                            <div>
                              <p className="font-semibold">{c.field}</p>
                              <p className="text-sm text-gray-600">
                                by {c.author} • {formatDateTime(c.date)} ({timeAgo(c.date)})
                              </p>
                            </div>
                            {expanded ? (
                              <ChevronUp className="h-4 w-4 text-gray-500" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-gray-500" />
                            )}
                          </div>

                          {expanded && (
                            <div className="text-sm mt-2 border-t pt-2 space-y-1">
                              <p>
                                <strong>Previous:</strong> {c.previous}
                              </p>
                              <p>
                                <strong>New:</strong> {c.new}
                              </p>
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Similar Questions */}
            <Card>
              <CardHeader>
                <CardTitle>Similar Questions</CardTitle>
                <CardDescription>(Questions with semantic similarity)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loadingSimilar ? (
                  <p className="text-gray-500">Loading similar questions...</p>
                ) : similarQuestions.length === 0 ? (
                  <p className="text-gray-500">No similar questions found.</p>
                ) : (
                  similarQuestions.map((q) => (
                    <Card
                      key={q.question_id}
                      className="p-4 bg-gray-50 border border-gray-200"
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-sm">{Math.round(q.similarity * 100)}% match</span>
                        <Badge className={getDifficultyColor(q.difficulty)}>{q.difficulty}</Badge>
                      </div>
                      <p className="font-medium">{q.question_text}</p>
                      <p className="text-sm text-muted-foreground mt-1">{q.course_code} - {q.course_name}</p>
                      <div className="flex space-x-2 pt-3">
                        <Button variant="outline" size="sm" className="flex-1" onClick={() => handleViewDetails(q.question_id)}>
                          <Eye className="h-4 w-4 mr-1" /> View Details
                        </Button>
                        <Button size="sm" className="flex-1" onClick={() => handleAddToCart(q)} disabled={isInCart(q.question_id)}>
                          <Plus className="h-4 w-4 mr-1" />
                          {isInCart(q.question_id) ? "Added to Cart" : "Add to Cart"}
                        </Button>
                      </div>
                    </Card>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
