import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/tabs";
import { ArrowLeft, HelpCircle, Eye, Plus, ShoppingBasket, Edit } from "lucide-react";
import EditQuestion from "./edit_question.jsx";

export function QuestionDetails({ 
  questionId, 
  onBack = () => {}, 
  onViewQuestion, 
  onGoToQuestionCart, 
  onAddToCart,
  cartQuestions = []
}) {
  const [questionData, setQuestionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(true);
  const [usageHistory, setUsageHistory] = useState([]);
  const [changeHistory, setChangeHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
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
          axios.get(`http://localhost:5003/api/questions/${s.question_id}`).then((res) => ({
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

  // Fetch usage & change history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoadingHistory(true);
        const [usageRes, changeRes] = await Promise.all([
          axios.get(`http://localhost:5003/api/questions/${questionId}/usage-history`),
          axios.get(`http://localhost:5003/api/questions/${questionId}/change-history`),
        ]);
        setUsageHistory(usageRes.data.usage || []);
        setChangeHistory(changeRes.data.changes || []);
      } catch (err) {
        console.error("Error fetching history:", err);
      } finally {
        setLoadingHistory(false);
      }
    };
    if (questionId) fetchHistory();
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

  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

  const handleAddToCart = (question) => {
    if (!isInCart(question.question_id) && onAddToCart) {
      onAddToCart(question);
    }
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading question details...
      </div>
    );
  }

  if (!questionData) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Question not found.
      </div>
    );
  }

  // Show edit page if editing
  if (isEditing) {
    return (
      <EditQuestion
        questionId={questionId}
        questionData={questionData}
        onBack={() => setIsEditing(false)}
        onSave={(updated) => setQuestionData(updated)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
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

            <Button variant="ghost" onClick={onGoToQuestionCart} className="flex items-center space-x-2">
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
                <Button size="sm" variant="outline" onClick={() => setIsEditing(true)} className="flex items-center space-x-1">
                  <Edit className="h-4 w-4" />
                  <span>Edit</span>
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {questionData.context?.text && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900 whitespace-pre-line">
                    {questionData.context.text}
                    {questionData.context.attachments && questionData.context.attachments.length > 0 && (
                      <ul className="mt-2">
                        {questionData.context.attachments.map((att, idx) => (
                          <li key={idx}>
                            <a href={att.url} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                              {att.name}
                            </a>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
                <div className="text-gray-800 text-base font-medium">{questionData.question_text}</div>

                {/* Options */}
                {questionData.options && (
                  <ul className="mt-2 space-y-1">
                    {Object.entries(questionData.options).map(([key, value]) => (
                      <li key={key} className="flex items-center space-x-2">
                        <span className="font-semibold">{key}.</span>
                        <span>{value}</span>
                        {questionData.correct_answer === key && <span className="text-green-600 ml-2">✅</span>}
                      </li>
                    ))}
                  </ul>
                )}

                {/* Explanation */}
                {questionData.explanation && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-900 whitespace-pre-line">
                    <strong>Explanation:</strong> {questionData.explanation}
                  </div>
                )}

                {/* Concepts */}
                {questionData.concepts && questionData.concepts.length > 0 && (
                  <p className="text-sm text-gray-700 mt-3">
                    <strong>Concepts:</strong> {questionData.concepts.join(", ")}
                  </p>
                )}
              </CardContent>

              {/* Add to Cart */}
              <div className="p-4 border-t border-gray-200 flex justify-end">
                <Button
                  size="sm"
                  onClick={() => handleAddToCart(questionData)}
                  disabled={isInCart(questionData.question_id)}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  {isInCart(questionData.question_id) ? "Added to Preview" : "Add to Preview"}
                </Button>
              </div>
            </Card>

            {/* Usage & Change History */}
            <Card>
              <CardHeader>
                <CardTitle>Question Analytics & History</CardTitle>
                <CardDescription>(Detailed usage statistics and modification history)</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="usage">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="usage">Usage History</TabsTrigger>
                    <TabsTrigger value="changes">Change History</TabsTrigger>
                  </TabsList>

                  <TabsContent value="usage">
                    {loadingHistory ? (
                      <p className="text-sm text-gray-500 mt-2">Loading usage history...</p>
                    ) : usageHistory.length === 0 ? (
                      <p className="text-sm text-gray-500 mt-2">No usage history available.</p>
                    ) : (
                      <ul className="space-y-4 mt-2">
                        {usageHistory.map((u, idx) => (
                          <li key={idx} className="p-3 border border-gray-200 rounded bg-gray-50">
                            <p className="font-semibold">{u.assessment_name}</p>
                            <p className="text-sm text-gray-600">
                              {u.num_students} students • {u.course_code} • {u.instructor}
                            </p>
                            <p className="text-xs text-muted-foreground">{u.semester}</p>
                            <p className="text-xs text-muted-foreground">{u.date}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </TabsContent>

                  <TabsContent value="changes">
                    {loadingHistory ? (
                      <p className="text-sm text-gray-500 mt-2">Loading change history...</p>
                    ) : changeHistory.length === 0 ? (
                      <p className="text-sm text-gray-500 mt-2">No change history available.</p>
                    ) : (
                      <ul className="space-y-4 mt-2">
                        {changeHistory.map((c, idx) => (
                          <li key={idx} className="p-3 border border-gray-200 rounded bg-gray-50 space-y-1">
                            <p className="font-semibold">{c.field}</p>
                            <p className="text-sm text-gray-600">
                              by {c.author} • {c.date}
                            </p>
                            <div className="text-sm">
                              <p><strong>Previous:</strong> {c.previous}</p>
                              <p><strong>New:</strong> {c.new}</p>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </TabsContent>
                </Tabs>
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
                    <Card key={q.question_id} className="p-4 bg-gray-50 border border-gray-200">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-semibold text-sm">{Math.round(q.similarity * 100)}% match</span>
                        <Badge className={getDifficultyColor(q.difficulty)}>{q.difficulty}</Badge>
                      </div>
                      <p className="font-medium">{q.question_text}</p>
                      <p className="text-sm text-muted-foreground mt-1">{q.course_code} - {q.course_name}</p>
                      {q.concepts && q.concepts.length > 0 && (
                        <p className="text-sm text-gray-700 mt-2">{q.concepts.join(", ")}</p>
                      )}
                      <div className="flex space-x-2 pt-3">
                        <Button variant="outline" size="sm" className="flex-1" onClick={() => handleViewDetails(q.question_id)}>
                          <Eye className="h-4 w-4 mr-1" /> View Details
                        </Button>
                        <Button size="sm" className="flex-1" onClick={() => handleAddToCart(q)} disabled={isInCart(q.question_id)}>
                          <Plus className="h-4 w-4 mr-1" />
                          {isInCart(q.question_id) ? "Added to Preview" : "Add to Preview"}
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
