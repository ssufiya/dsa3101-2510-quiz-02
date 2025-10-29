import { useState, useEffect } from "react";
import axios from "axios";
import {
  Card,
  CardContent,
  CardHeader,
} from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import {
  ArrowLeft,
  Eye,
  Plus,
  ShoppingBasket,
  Edit,
} from "lucide-react";
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
  const [versions, setVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  // --- Fetch question details ---
  const fetchQuestionData = async (id) => {
    setLoading(true);
    const response = await axios.get(`http://localhost:5003/api/questions/${id}`);
    setQuestionData(response.data.data);
    setLoading(false);
  };

  useEffect(() => {
    if (questionId) fetchQuestionData(questionId);
  }, [questionId]);

  // --- Fetch similar questions ---
  useEffect(() => {
    const fetchSimilarQuestions = async () => {
      setLoadingSimilar(true);
      const res = await axios.get(
        `http://localhost:5003/api/questions/${questionId}/suggestions?top_n=5`
      );
      const suggested = res.data.suggested_variants || [];
      const details = await Promise.all(
        suggested.map((s) =>
          axios
            .get(`http://localhost:5003/api/questions/${s.question_id}`)
            .then((r) => ({ ...r.data.data, similarity: s.similarity }))
        )
      );
      setSimilarQuestions(details);
      setLoadingSimilar(false);
    };
    if (questionId) fetchSimilarQuestions();
  }, [questionId]);

  // --- Fetch version history ---
  const fetchVersions = async (id) => {
    setLoadingVersions(true);
    try {
      const res = await axios.get(`http://localhost:5003/api/questions/${id}/versions`);
      const sorted = (res.data.data || []).sort((a, b) => b.version_number - a.version_number);
      setVersions(sorted);
    } finally {
      setLoadingVersions(false);
    }
  };

  useEffect(() => {
    if (questionId) fetchVersions(questionId);
  }, [questionId]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case "low":
      case "easy":
        return "bg-green-100 text-green-800";
      case "med":
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "high":
      case "hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

  const handleAddToCart = (question) => {
    if (!isInCart(question.question_id) && onAddToCart) onAddToCart(question);
  };

  const handleViewDetails = async (id) => {
    await fetchQuestionData(id);
    await fetchVersions(id);
    window.scrollTo({ top: 0, behavior: "smooth" });
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
        onSave={(updated, parentId) => {
          setIsEditing(false);
          handleViewDetails(parentId);
        }}
      />
    );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 shadow-sm relative">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between relative">
          {/* LEFT: Back button */}
          <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Back</span>
          </Button>

          {/* CENTER: Title */}
          <h1 className="absolute left-1/2 transform -translate-x-1/2 text-xl font-semibold text-gray-800">
            Question Details
          </h1>

          {/* RIGHT: Cart button */}
          <Button variant="ghost" onClick={onGoToQuestionCart} className="flex items-center space-x-2">
            <ShoppingBasket className="h-5 w-5" />
            <span>Cart ({cartQuestions.length})</span>
          </Button>
        </div>
        <div className="border-t border-gray-100"></div>
      </header>

      {/* MAIN CONTENT */}
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-10">
        {/* Question Info */}
        <Card className="shadow-md border border-gray-200">
          <CardHeader className="flex justify-between items-center border-b pb-3">
            <div>
              <h1 className="text-2xl font-semibold mb-1 text-gray-900">
                {questionData.course_code} – {questionData.course_name}
              </h1>
              <p className="text-sm text-gray-500">
                ID: {questionData.question_id} | {questionData.assessment_type}
              </p>
              {questionData.difficulty && (
                <Badge className={`mt-2 ${getDifficultyColor(questionData.difficulty)}`}>
                  {questionData.difficulty}
                </Badge>
              )}
            </div>

            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                <Edit className="h-4 w-4 mr-1" /> Edit
              </Button>
              <Button
                size="sm"
                onClick={() => handleAddToCart(questionData)}
                disabled={isInCart(questionData.question_id)}
              >
                <Plus className="h-4 w-4 mr-1" />
                {isInCart(questionData.question_id) ? "Added" : "Add to Cart"}
              </Button>
            </div>
          </CardHeader>

          <CardContent className="py-6 space-y-4">
            <p className="text-gray-800 text-base leading-relaxed">{questionData.question_text}</p>

            {questionData.options && (
              <ul className="space-y-2 pl-2">
                {Object.entries(questionData.options).map(([key, value]) => (
                  <li key={key} className="flex items-start space-x-2">
                    <span className="font-semibold">{key}.</span>
                    <span>{value}</span>
                    {questionData.correct_answer === key && (
                      <span className="text-green-600 ml-1">✔</span>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {questionData.explanation && (
              <div className="bg-yellow-50 border border-yellow-200 p-3 rounded text-sm text-yellow-900">
                <strong>Explanation:</strong> {questionData.explanation}
              </div>
            )}

            {questionData.concepts?.length > 0 && (
              <p className="text-sm text-gray-600">
                <strong>Concepts:</strong> {questionData.concepts.join(", ")}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Version History */}
        <section className="max-w-3xl mx-auto w-full">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Change History</h2>
          {loadingVersions ? (
            <p className="text-gray-500">Loading...</p>
          ) : versions.length === 0 ? (
            <p className="text-gray-500">No version history available.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {versions.map((v) => (
                <Card key={v.question_id} className="shadow-sm hover:shadow-md transition-all">
                  <CardHeader className="pb-1">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-semibold">
                        Version {v.version_number}{" "}
                        {v.is_latest && <span className="text-green-600 text-xs">(Latest)</span>}
                      </h3>
                      <p className="text-xs text-gray-400">
                        {new Date(v.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </CardHeader>
                  <CardContent className="text-sm space-y-2">
                    <p className="italic text-gray-800 line-clamp-2">
                      {v.question_text || "No text available"}
                    </p>
                    <div className="text-gray-600">
                      <p>
                        <strong>Course:</strong> {v.course_code || "—"}
                      </p>
                      <p>
                        <strong>Difficulty:</strong>{" "}
                        <Badge className={getDifficultyColor(v.difficulty)}>
                          {v.difficulty || "—"}
                        </Badge>
                      </p>
                    </div>
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(v.question_id)}
                      >
                        <Eye className="h-4 w-4 mr-1" /> View
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Similar Questions */}
        <section className="max-w-3xl mx-auto w-full">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Similar Questions</h2>
          {loadingSimilar ? (
            <p className="text-gray-500">Loading...</p>
          ) : similarQuestions.length === 0 ? (
            <p className="text-gray-500">No similar questions found.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {similarQuestions.map((q) => (
                <Card key={q.question_id} className="shadow-sm hover:shadow-md transition">
                  <CardContent className="p-4 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">
                        {Math.round(q.similarity * 100)}% match
                      </span>
                      <Badge className={getDifficultyColor(q.difficulty)}>
                        {q.difficulty}
                      </Badge>
                    </div>
                    <p className="font-medium text-gray-900 line-clamp-2">{q.question_text}</p>
                    <p className="text-sm text-gray-500">
                      {q.course_code} – {q.course_name}
                    </p>
                    <div className="flex space-x-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(q.question_id)}
                        className="flex-1"
                      >
                        <Eye className="h-4 w-4 mr-1" /> View
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAddToCart(q)}
                        disabled={isInCart(q.question_id)}
                        className="flex-1"
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        {isInCart(q.question_id) ? "Added" : "Add"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}