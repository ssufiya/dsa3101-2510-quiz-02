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
      <header className="bg-white border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          {/* TOP ROW: Back + Cart */}
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </Button>

            <Button
              variant="ghost"
              onClick={onGoToQuestionCart}
              className="flex items-center space-x-2"
            >
              <ShoppingBasket className="h-5 w-5" />
              <span>Cart ({cartQuestions.length})</span>
            </Button>
          </div>


          {/* BOTTOM ROW: Title */}
          <h1 
          className="text-center mt-4 text-xl font-semibold text-gray-800" 
          style={{ fontWeight: "600"}}
          >
            Question Details
          </h1>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-10">
        {/* --- Concepts Section --- */}
        {Array.isArray(questionData.concepts) && questionData.concepts.length > 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "flex-start",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
              fontSize: "14px",
              color: "#000",
            }}
          >
            <span style={{ fontWeight: "500", marginRight: "8px" }}>Concepts:</span>
            {questionData.concepts.slice(0, 3).map((tag, idx) => (
              <span
                key={idx}
                style={{
                  backgroundColor: "#f0f0f0",
                  borderRadius: "16px",
                  padding: "6px 12px",
                  fontSize: "14px",
                  border: "1px solid #ddd",
                }}
              >
                {tag.trim()}
              </span>
            ))}
          </div>
        )}

        {/* --- Question Info --- */}
        <div className="bg-white p-6 rounded-lg shadow-sm border-gray-200">
          <div className="flex justify-between items-center pb-3 mb-4">
            <div>
              <h1 className="text-[30px] font-medium mb-2 text-gray-800 pl-4">
                {questionData.course_code} – {questionData.course_name}
              </h1>
              <p className="capitalize pl-4">
                Question: {questionData.question_id} | {questionData.question_type} |{" "}
                {questionData.difficulty}
              </p>
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
          </div>

          {/* --- Question Box --- */}
          <div className="mb-6">
            <p className="text-gray-800 text-base leading-relaxed mb-4" >
              {questionData.question_text}
            </p>

            {questionData.options && (
              <ul className="space-y-2 mb-4" >
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
          </div>

          {/* --- Explanation Box --- */}
          {questionData.explanation && (
            <div className="mb-6" >
              <strong>Explanation:</strong> {questionData.explanation}
            </div>
          )}
        </div>

        {/* --- Version History --- */}
        <section className="max-w-3xl mx-auto w-full">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Change History</h2>
          {loadingVersions ? (
            <p className="text-gray-500">Loading...</p>
          ) : versions.length === 0 ? (
            <p className="text-gray-500">No version history available.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {versions
                .slice()
                .sort((a, b) => a.version_number - b.version_number)
                .map((v) => (
                  <Card
                    key={v.question_id}
                    className={`shadow-sm transition-all ${
                      v.is_latest ? "bg-gray-100 text-gray-600" : "hover:shadow-md"
                    }`}
                    style={{borderRadius: '16px', overflow: 'hidden'}}
                  >
                    <CardHeader className="pb-1" style={{paddingLeft: '20px'}}>
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-semibold">
                          Version {v.version_number}{" "}
                          {v.is_latest && (
                            <span className="text-gray-500 text-xs">(Latest)</span>
                          )}
                        </h3>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewDetails(v.question_id)}
                          className="h-7 px-1 text-xs"
                        >
                          <Eye className="h-3 w-3 mr-1" /> View
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="text-sm space-y-2" style={{paddingLeft: '20px'}}>
                      <p className="text-gray-800 line-clamp-2">
                        {v.question_text || "No text available"}
                      </p>
                      <div className="text-gray-600 space-y-1">
                        <p>
                          <span>Course:</span> {v.course_code} | <span>Type:</span> {v.question_type} |{" "}
                          <span>Difficulty:</span>{" "}
                          {v.difficulty
                            ? v.difficulty.charAt(0).toUpperCase() +
                              v.difficulty.slice(1).toLowerCase()
                            : "—"}
                        </p>
                      </div>
                      {/* Bottom timestamp */}
                      <p className="text-xs text-gray-300 mt-4">
                        Updated {new Date(v.created_at).toLocaleString()}
                      </p>
                    </CardContent>
                  </Card>
                ))}
            </div>
          )}
        </section>

        {/* --- Similar Questions --- */}
        <section className="max-w-3xl mx-auto w-full">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Similar Questions</h2>
          {loadingSimilar ? (
            <p className="text-gray-500">Loading...</p>
          ) : similarQuestions.length === 0 ? (
            <p className="text-gray-500">No similar questions found.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2" style={{ gap: '32px' }}>
              {similarQuestions.map((q) => (
                <Card
                  key={q.question_id}
                  className="shadow-sm hover:shadow-md transition"
                  style={{ borderRadius: '16px', overflow: 'hidden' }}
                >
                  {/* ADJUSTED: Increased Top Padding on CardContent and removed left padding */}
                  <CardContent className="p-4 space-y-2" style={{ paddingTop: '20px', paddingBottom: '16px' }}>
                    
                    {/* START: Combined Concept and Match Line */}
                    <div
                      className="flex justify-between items-start"
                    >
                      {/* Concepts (Left side) */}
                      {Array.isArray(q.concepts) && q.concepts.length > 0 && (
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "flex-start",
                            alignItems: "center",
                            flexWrap: "wrap",
                            gap: "8px",
                            fontSize: "14px",
                            color: "#000",
                            maxWidth: '80%',
                            marginLeft: '4px', // Tweak: Moves concepts slightly left

                          }}
                        >
                          {q.concepts.slice(0, 3).map((tag, idx) => (
                            <span
                              key={idx}
                              style={{
                                backgroundColor: "#f0f0f0",
                                borderRadius: "16px",
                                padding: "6px 12px",
                                fontSize: "14px",
                                border: "1px solid #ddd",
                              }}
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                      {/* % Match (Right side) */}
                      <span className="text-sm font-medium text-gray-700 italic" style={{ marginRight: '4px'}}>
                        {Math.round(q.similarity * 100)}% match
                      </span>
                    </div>
                    {/* END: Combined Concept and Match Line */}

                    {/* Question text and details - Added a top margin to separate from the line above */}
                    <p className="font-medium text-gray-900 line-clamp-2" style={{ marginTop: '12px', marginLeft: '6px'}}>
                      {q.question_text}
                    </p>
                    <p className="text-sm text-gray-500" style={{ marginLeft: '6px'}}>
                      <span>Course:</span> {q.course_code} | <span>Type:</span> {q.question_type} |{" "}
                      <span>Difficulty:</span>{" "}
                      {q.difficulty
                        ? q.difficulty.charAt(0).toUpperCase() +
                          q.difficulty.slice(1).toLowerCase()
                        : "—"}
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