import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { ArrowLeft, Eye, Plus, BarChart3, GripVertical, HelpCircle } from "lucide-react";
import axios from "axios";

function QuestionCard({ question, onQuestionDetails, onAddToPreview }) {
  const getTypeColor = (type) => {
    switch (type) {
      case "MCQ":
      case "Multiple Choice":
        return "bg-blue-100 text-blue-800";
      case "True/False":
        return "bg-purple-100 text-purple-800";
      case "Short Answer":
        return "bg-orange-100 text-orange-800";
      case "Essay":
        return "bg-pink-100 text-pink-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-2">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
            <Badge className={getTypeColor(question.question_type)}>
              {question.question_type}
            </Badge>
          </div>
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <BarChart3 className="h-4 w-4" />
            <span>{question.usageCount || 0}</span>
          </div>
        </div>
        <CardTitle className="text-lg leading-relaxed">
          {question.assessment_type || "—"}
        </CardTitle>
        <CardDescription>
          <span className="block font-medium text-foreground">
            {question.course_code}
          </span>
          <span className="block text-sm text-muted-foreground">
            Difficulty: {question.difficulty}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground line-clamp-3">
            {question.question_text}
          </div>

          {question.concepts && (
            <div className="flex flex-wrap gap-1">
              {question.concepts
                .split(",")
                .slice(0, 3)
                .map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {tag.trim()}
                  </Badge>
                ))}
            </div>
          )}

          <div className="flex space-x-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onQuestionDetails(question.question_id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              View Details
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAddToPreview(question.question_id)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Add to Preview
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function QuestionLibrary({ onBack, onQuestionDetails }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState("all");
  const [selectedCourse, setSelectedCourse] = useState("all");
  const [selectedType, setSelectedType] = useState("all");
  const [questions, setQuestions] = useState([]);
  const [previewQuestions, setPreviewQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  const difficulties = ["all", "Easy", "Medium", "Hard"];
  const types = ["all", "MCQ", "True/False", "Short Answer", "Essay"];

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true);
        const response = await axios.get("http://localhost:8000/api/questions/", {
          params: {
            difficulty: selectedDifficulty !== "all" ? selectedDifficulty : null,
            subject: selectedCourse !== "all" ? selectedCourse : null,
            topic: searchTerm || null,
            is_latest: true,
          },
        });
        setQuestions(response.data.data || []);
      } catch (error) {
        console.error("Error fetching questions:", error);
      } finally {
        setLoading(false);
      }
    };

      fetchQuestions();
}, [selectedDifficulty, selectedType, selectedCourse, searchTerm]);

  const addToPreview = (questionId) => {
    const question = questions.find((q) => q.question_id === questionId);
    if (question && !previewQuestions.find((q) => q.question_id === questionId)) {
      setPreviewQuestions((prev) => [...prev, question]);
    }
  };

return (
  <div className="min-h-screen bg-gray-50 flex">
    {/* Main Section */}
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 space-x-4">
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Dashboard</span>
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
            <div className="flex items-center space-x-3">
              <div className="bg-primary rounded-lg p-2">
                <HelpCircle className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Question Library</h1>
                <p className="text-sm text-muted-foreground">
                  Browse questions from the database
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap gap-4">
        <Input
          placeholder="Search by keyword..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-64"
        />

        <select
          className="border border-gray-300 rounded-md px-2 py-1"
          value={selectedDifficulty}
          onChange={(e) => setSelectedDifficulty(e.target.value)}
        >
          {difficulties.map((dif) => (
            <option key={dif} value={dif}>
              {dif}
            </option>
          ))}
        </select>

        <select
          className="border border-gray-300 rounded-md px-2 py-1"
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
        >
          {types.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        {/* Example static course list — can be replaced with /courses API */}
        <select
          className="border border-gray-300 rounded-md px-2 py-1"
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
        >
          <option value="all">all</option>
          <option value="DSA1101">DSA1101</option>
          <option value="CS1010">CS1010</option>
        </select>
      </div>

      {/* Question list */}
      <div className="p-6">
        {loading ? (
          <p>Loading questions...</p>
        ) : !questions || questions.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <p>No questions found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {questions.map((q) => (
              <QuestionCard
                key={q.question_id}
                question={q}
                onQuestionDetails={onQuestionDetails}
                onAddToPreview={addToPreview}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  </div>
);
}
