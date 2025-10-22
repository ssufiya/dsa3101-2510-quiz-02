import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/tabs";
import { ArrowLeft, HelpCircle, Eye, Plus } from "lucide-react";

export function QuestionDetails({ questionId, onBack = () => {}, onViewQuestion }) {
  const [questionData, setQuestionData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(true);

  const [usageHistory, setUsageHistory] = useState([]);
  const [changeHistory, setChangeHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const [previewQuestions, setPreviewQuestions] = useState([]); 

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

  // handle add to preview
  const handleAddToPreview = (question) => {
    if (!previewQuestions.find((q) => q.question_id === question.question_id)) {
      setPreviewQuestions((prev) => [...prev, question]);
    }
  };

  // handle view details
  const handleViewDetails = (id) => {
    if (onViewQuestion) {
      onViewQuestion(id); // delegate to parent
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
      setLoading(true);
      axios
        .get(`http://localhost:5003/api/questions/${id}`)
        .then((res) => setQuestionData(res.data.data))
        .finally(() => setLoading(false));
    }
  };

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 space-x-4">
            <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Library</span>
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
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
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Section */}
          <div className="flex-1 space-y-6">
            {/* Question Card */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between mb-4">
                  <Badge className={getDifficultyColor(questionData.difficulty)}>
                    {questionData.difficulty}
                  </Badge>
                </div>
                <CardTitle>{questionData.assessment_type}</CardTitle>
                <CardDescription>{questionData.question_type}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {questionData.context?.context_text && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900 whitespace-pre-line">
                    {questionData.context.context_text}
                  </div>
                )}
                <div className="text-gray-800 text-base font-medium">{questionData.question_text}</div>

                {Array.isArray(questionData.concepts) && questionData.concepts.length > 0 && (
                  <p className="text-sm text-gray-700 mt-3">
                    {questionData.concepts.map((c) => c.trim()).join(", ")}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Analytics & History */}
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

                  {/* Usage History */}
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

                  {/* Change History */}
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
                              <p>
                                <strong>Previous:</strong> {c.previous}
                              </p>
                              <p>
                                <strong>New:</strong> {c.new}
                              </p>
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
                <CardDescription>
                  (Questions with semantic similarity based on content and context)
                </CardDescription>
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
                        <span className="font-semibold text-sm">
                          {Math.round(q.similarity * 100)}% match
                        </span>
                        <Badge className={getDifficultyColor(q.difficulty)}>
                          {q.difficulty}
                        </Badge>
                      </div>

                      <p className="font-medium">{q.question_text}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {q.course_code} - {q.course_name}
                      </p>

                      {q.concepts && q.concepts.length > 0 && (
                        <p className="text-sm text-gray-700 mt-2">
                          {q.concepts.map((c) => c.trim()).join(", ")}
                        </p>
                      )}

                      {/* Buttons added here */}
                      <div className="flex space-x-2 pt-3">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => handleViewDetails(q.question_id)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View Details
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1"
                          onClick={() => handleAddToPreview(q)}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add to Preview
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
