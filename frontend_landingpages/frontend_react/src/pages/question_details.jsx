import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/tabs";
import {
  ArrowLeft,
  BarChart3,
  Edit3,
  Download,
  Eye,
  HelpCircle,
  Lightbulb,
} from "lucide-react";

export function QuestionDetails({ questionId, onBack = () => {}, onViewQuestion }) {
  const [questionData, setQuestionData] = useState(null);
  const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchQuestionData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5003/api/questions/${questionId}`);
      setQuestionData(response.data.data); // not response.data.data || []
    } catch (error) {
      console.error("Error fetching question:", error);
    } finally {
      setLoading(false);
    }
  };

  if (questionId) {
    fetchQuestionData();
  }
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
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between mb-4">
                  <Badge className={getDifficultyColor(questionData.difficulty)}>
                    {questionData.difficulty}
                  </Badge>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Edit3 className="h-4 w-4 mr-2" /> Edit
                    </Button>
                    <Button size="sm">
                      <Download className="h-4 w-4 mr-2" /> Import
                    </Button>
                  </div>
                </div>
                <CardTitle>{questionData.assessment_type}</CardTitle>
                <CardDescription>{questionData.question_type}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Context */}
                {questionData.context?.context_text && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900 whitespace-pre-line">
                    {questionData.context.context_text}
                  </div>
                )}

                {/* Question Text */}
                <div className="text-gray-800 text-base font-medium">
                  {questionData.question_text}
                </div>

                {/* Concepts */}
                {Array.isArray(questionData.concepts) && questionData.concepts.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {questionData.concepts.map((c, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {c.trim()}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Analytics Tabs placeholder */}
            <Card>
              <CardHeader>
                <CardTitle>Question Analytics & History</CardTitle>
                <CardDescription>No analytics data available yet.</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="usage">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="usage">Usage</TabsTrigger>
                    <TabsTrigger value="changes">Changes</TabsTrigger>
                  </TabsList>
                  <TabsContent value="usage">
                    <p className="text-sm text-gray-500 mt-2">Usage data unavailable.</p>
                  </TabsContent>
                  <TabsContent value="changes">
                    <p className="text-sm text-gray-500 mt-2">Change history unavailable.</p>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Section */}
          <aside className="w-full md:w-1/3 space-y-6 mt-6 md:mt-0">
            <Card>
              <CardHeader>
                <CardTitle>Question Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Course Code</span>
                  <p className="font-medium">{questionData.course_code}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Course Name</span>
                  <p className="font-medium">{questionData.course_name}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Assessment Type</span>
                  <p className="font-medium">{questionData.assessment_type}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Version</span>
                  <p className="font-medium">{questionData.version_number}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Created At</span>
                  <p className="font-medium">
                    {new Date(questionData.created_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Tags section */}
            {questionData.tags && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Lightbulb className="h-5 w-5" />
                    <span>Tags</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-1">
                  {Array.isArray(questionData.tags.concepts)
                    ? questionData.tags.concepts.map((tag, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {tag.trim()}
                        </Badge>
                      ))
                    : Object.entries(questionData.tags).map(([k, v]) => (
                        <Badge key={k} variant="secondary" className="text-xs">
                          {`${k}: ${v}`}
                        </Badge>
                      ))}
                </CardContent>
              </Card>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
