import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/tabs";
import {
  ArrowLeft,
  Clock,
  BarChart3,
  Calendar,
  Edit3,
  Download,
  Eye,
  HelpCircle,
  Lightbulb,
  ExternalLink
} from "lucide-react";

export function QuestionDetails({ questionId, onBack, onViewQuestion }) {
  // Default to a mock question if no questionId is provided
  const [questionData] = useState({
    id: "q-1",
    question:
      "What is the time complexity of inserting an element at the beginning of a linked list?",
    type: "Multiple Choice",
    options: ["O(1)", "O(n)", "O(log n)", "O(n²)"],
    correctAnswer: "O(1)",
    explanation:
      "Inserting at the beginning of a linked list only requires updating the head pointer and setting the new node's next pointer, which takes constant time.",
    courseName: "Data Structures and Algorithms",
    courseCode: "CS 201",
    difficulty: "Medium",
    author: "Dr. Sarah Chen",
    institution: "Stanford University",
    createdAt: "2024-01-12",
    lastModified: "2024-01-15",
    tags: ["linked-list", "time-complexity", "algorithms"],
    subject: "Computer Science",
    totalUsages: 245,
    uniqueInstructors: 8,
    averageScore: 72.5,
    lastUsed: "2024-01-15",
  });

  const [usageHistory] = useState([
    {
      id: "usage-1",
      semester: "Spring",
      year: 2024,
      course: "CS 201",
      instructor: "Dr. Sarah Chen",
      usageCount: 45,
      date: "2024-01-15",
      quizTitle: "Midterm Exam - Data Structures",
    },
    {
      id: "usage-2",
      semester: "Fall",
      year: 2023,
      course: "CS 201",
      instructor: "Dr. Sarah Chen",
      usageCount: 52,
      date: "2023-10-20",
      quizTitle: "Quiz 3 - Linked Lists and Arrays",
    },
  ]);

  const [editHistory] = useState([
    {
      id: "edit-1",
      date: "2024-01-15",
      editor: "Dr. Sarah Chen",
      changeType: "Correct Answer",
      description: "Updated correct answer explanation for clarity",
      previousValue: "Inserting at the beginning takes constant time.",
      newValue:
        "Inserting at the beginning of a linked list only requires updating the head pointer and setting the new node's next pointer, which takes constant time.",
    },
  ]);

  const [similarQuestions] = useState([
    {
      id: "sq-1",
      question: "What is the time complexity of deleting an element from the end of a linked list?",
      courseName: "Data Structures and Algorithms",
      courseCode: "CS 201",
      difficulty: "Medium",
      type: "Multiple Choice",
      author: "Dr. Sarah Chen",
      institution: "Stanford University",
      usageCount: 189,
      tags: ["linked-list", "time-complexity", "algorithms"],
      subject: "Computer Science",
      similarityScore: 95,
      similarityReasons: ["Same course", "Identical tags", "Similar time complexity focus"],
    },
  ]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case "Easy":
        return "bg-green-100 text-green-800";
      case "Medium":
        return "bg-yellow-100 text-yellow-800";
      case "Hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getChangeTypeColor = (changeType) => {
    switch (changeType) {
      case "Created":
        return "bg-green-100 text-green-800";
      case "Question Text":
        return "bg-blue-100 text-blue-800";
      case "Options":
        return "bg-purple-100 text-purple-800";
      case "Correct Answer":
        return "bg-orange-100 text-orange-800";
      case "Difficulty":
        return "bg-yellow-100 text-yellow-800";
      case "Tags":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

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
                <h1 className="text-xl">Question Details</h1>
                <p className="text-sm text-muted-foreground">
                  {questionData.courseCode} - {questionData.courseName}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Question card and analytics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Question card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Badge className={getDifficultyColor(questionData.difficulty)}>
                      {questionData.difficulty}
                    </Badge>
                    <Badge className="bg-blue-100 text-blue-800">{questionData.type}</Badge>
                  </div>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Import
                    </Button>
                  </div>
                </div>
                <CardTitle className="text-xl leading-relaxed">{questionData.question}</CardTitle>
                <CardDescription>
                  <span className="flex items-center space-x-4 text-sm">
                    <span>By {questionData.author}</span>
                    <span>•</span>
                    <span>{questionData.institution}</span>
                    <span>•</span>
                    <span>Created {new Date(questionData.createdAt).toLocaleDateString()}</span>
                  </span>
                </CardDescription>
              </CardHeader>

              {/* Options */}
              {questionData.type === "Multiple Choice" && (
                <CardContent className="space-y-3">
                  {questionData.options.map((option, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border ${
                        option === questionData.correctAnswer
                          ? "bg-green-50 border-green-200"
                          : "bg-gray-50 border-gray-200"
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">{String.fromCharCode(65 + index)}.</span>
                        <span>{option}</span>
                        {option === questionData.correctAnswer && (
                          <Badge className="text-xs bg-green-100 text-green-800">Correct</Badge>
                        )}
                      </div>
                    </div>
                  ))}

                  {/* Explanation */}
                  {questionData.explanation && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h5 className="font-medium text-blue-900 mb-2">Explanation:</h5>
                      <p className="text-blue-800 text-sm">{questionData.explanation}</p>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>

            {/* Tabs for Usage & Edit History */}
            <Card>
              <CardHeader>
                <CardTitle>Question Analytics & History</CardTitle>
                <CardDescription>
                  Detailed usage statistics and modification history
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="usage">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="usage">Usage History</TabsTrigger>
                    <TabsTrigger value="changes">Change History</TabsTrigger>
                  </TabsList>

                  <TabsContent value="usage" className="space-y-3">
                    {usageHistory.map((u) => (
                      <Card key={u.id} className="p-3 border">
                        <p className="text-sm font-medium">{u.quizTitle}</p>
                        <p className="text-xs text-muted-foreground">
                          {u.course} • {u.instructor} • {u.semester} {u.year} • Used {u.usageCount} times
                        </p>
                      </Card>
                    ))}
                  </TabsContent>

                  <TabsContent value="changes" className="space-y-3">
                    {editHistory.map((e) => (
                      <Card key={e.id} className="p-3 border">
                        <Badge className={getChangeTypeColor(e.changeType)}>{e.changeType}</Badge>
                        <p className="text-sm">{e.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {e.previousValue} → {e.newValue}
                        </p>
                      </Card>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Similar Questions Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Similar Questions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {similarQuestions.map((sq) => (
                  <Card key={sq.id} className="p-3 border cursor-pointer" onClick={() => onViewQuestion?.(sq.id)}>
                    <p className="text-sm font-medium">{sq.question}</p>
                    <p className="text-xs text-muted-foreground">
                      {sq.courseCode} • {sq.courseName} • {sq.difficulty}
                    </p>
                  </Card>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
