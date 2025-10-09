import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle,} from "../components/card";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { ArrowLeft, Eye, Plus, X, FileText, BarChart3, GripVertical, HelpCircle,} from "lucide-react";
import { ScrollArea } from "../components/scrollarea";

// Question card component (no drag)
function QuestionCard({ question, onViewQuestion, onAddToPreview }) {
  const getTypeColor = (type) => {
    switch (type) {
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
            <Badge className={getTypeColor(question.type)}>{question.type}</Badge>
          </div>
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <BarChart3 className="h-4 w-4" />
            <span>{question.usageCount}</span>
          </div>
        </div>
        <CardTitle className="text-lg leading-relaxed">
          {question.academicYear} {question.examType}
        </CardTitle>
        <CardDescription>
          <span className="block font-medium text-foreground">
            {question.courseCode} - {question.courseName}
          </span>
          <span className="block text-sm">
            {question.author} • {question.institution}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground line-clamp-3">
            {question.question}
          </div>

          <div className="text-sm text-muted-foreground">
            Subject: {question.subject}
          </div>

          <div className="flex flex-wrap gap-1">
            {question.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {question.tags.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{question.tags.length - 3}
              </Badge>
            )}
          </div>

          <div className="flex space-x-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onViewQuestion(question.id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              View Details
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAddToPreview(question.id)}
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

// Preview area (no drop zone)
function PreviewArea({ previewQuestions, onRemoveFromPreview, onClearPreview }) {
  return (
    <div className="w-80 bg-white border-l border-gray-200 h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Question Preview</span>
          </h3>
          {previewQuestions.length > 0 && (
            <Button variant="ghost" size="sm" onClick={onClearPreview}>
              Clear All
            </Button>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {previewQuestions.length} question
          {previewQuestions.length !== 1 ? "s" : ""} selected
        </p>
      </div>

      <div className="flex-1 p-4">
        {previewQuestions.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h4 className="mb-2">No questions selected</h4>
            <p className="text-sm text-muted-foreground">
              Use "Add to Preview" to select questions.
            </p>
          </div>
        ) : (
          <ScrollArea className="h-full">
            <div className="space-y-4">
              {previewQuestions.map((question, index) => (
                <Card key={question.id} className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2 h-6 w-6 p-0"
                    onClick={() => onRemoveFromPreview(question.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <CardHeader className="pb-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-muted-foreground">
                        Q{index + 1}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {question.type}
                      </Badge>
                    </div>
                    <CardDescription className="text-xs">
                      {question.courseCode} - {question.courseName}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-sm line-clamp-3">{question.question}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>

      {previewQuestions.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <Button className="w-full">Create Quiz from Preview</Button>
        </div>
      )}
    </div>
  );
}

export function Library({ onBack, onViewQuestion }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("all");
  const [selectedDifficulty, setSelectedDifficulty] = useState("all");
  const [selectedCourse, setSelectedCourse] = useState("all");
  const [selectedType, setSelectedType] = useState("all");
  const [previewQuestions, setPreviewQuestions] = useState([]);

  const [libraryQuestions] = useState([
    // sample data
    {
      id: 1,
      academicYear: "2024",
      examType: "Midterm",
      courseCode: "CS1010",
      courseName: "Programming Methodology",
      author: "Dr. Tan",
      institution: "NUS",
      question: "Explain the difference between pass-by-value and pass-by-reference.",
      subject: "Computer Science",
      difficulty: "Medium",
      usageCount: 10,
      type: "Short Answer",
      tags: ["functions", "parameters", "C"],
    },
    {
      id: 2,
      academicYear: "2023",
      examType: "Final",
      courseCode: "MA1101R",
      courseName: "Linear Algebra I",
      author: "Prof. Lim",
      institution: "NUS",
      question: "State and prove the Rank-Nullity Theorem.",
      subject: "Mathematics",
      difficulty: "Hard",
      usageCount: 5,
      type: "Essay",
      tags: ["theorem", "proof", "linear algebra"],
    },
  ]);

  const addToPreview = (questionId) => {
    const question = libraryQuestions.find((q) => q.id === questionId);
    if (question && !previewQuestions.find((q) => q.id === questionId)) {
      setPreviewQuestions((prev) => [...prev, question]);
    }
  };

  const removeFromPreview = (id) =>
    setPreviewQuestions((prev) => prev.filter((q) => q.id !== id));

  const clearPreview = () => setPreviewQuestions([]);

  const filteredQuestions = libraryQuestions.filter((q) => {
    const matchesSearch =
      q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.courseName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.courseCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.tags.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesSubject = selectedSubject === "all" || q.subject === selectedSubject;
    const matchesDifficulty =
      selectedDifficulty === "all" || q.difficulty === selectedDifficulty;
    const matchesCourse =
      selectedCourse === "all" ||
      `${q.courseCode} - ${q.courseName}` === selectedCourse;
    const matchesType = selectedType === "all" || q.type === selectedType;

    return (
      matchesSearch &&
      matchesSubject &&
      matchesDifficulty &&
      matchesCourse &&
      matchesType
    );
  });

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Main Section */}
      <div className="flex-1 flex flex-col">
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
                  <h1 className="text-xl">Question Library</h1>
                  <p className="text-sm text-muted-foreground">
                    Browse questions from other professors
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Question list */}
        <div className="p-6 grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {filteredQuestions.map((q) => (
            <QuestionCard
              key={q.id}
              question={q}
              onViewQuestion={onViewQuestion}
              onAddToPreview={addToPreview}
            />
          ))}
        </div>
      </div>

      <PreviewArea
        previewQuestions={previewQuestions}
        onRemoveFromPreview={removeFromPreview}
        onClearPreview={clearPreview}
      />
    </div>
  );
}
