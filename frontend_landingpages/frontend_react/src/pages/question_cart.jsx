import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { ArrowLeft, Trash2 } from "lucide-react";

export function QuestionCart({ onBack, onBackToLibrary, onBackToDetails, questions, onRemoveQuestion }) {
  const [localQuestions, setLocalQuestions] = useState([]);

  useEffect(() => {
    // Sync cart questions from props
    setLocalQuestions(questions || []);
  }, [questions]);

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

  return (
    <div className="p-6 space-y-4 min-h-screen bg-gray-50">
      {/* Navigation Buttons */}
      <div className="flex space-x-2">
        <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Button>
        {onBackToLibrary && (
          <Button variant="ghost" onClick={onBackToLibrary} className="flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Library</span>
          </Button>
        )}
        {onBackToDetails && (
          <Button variant="ghost" onClick={onBackToDetails} className="flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Question</span>
          </Button>
        )}
      </div>

      <h2 className="text-xl font-bold mt-4">Preview Selected Questions</h2>

      {localQuestions.length === 0 ? (
        <p className="text-gray-500 mt-4">No questions in your cart yet.</p>
      ) : (
        <div className="grid gap-4 mt-4">
          {localQuestions.map((q) => (
            <Card key={q.question_id} className="shadow-sm">
              <CardHeader className="flex justify-between items-center">
                <div className="flex flex-col">
                  <CardTitle className="text-sm">Question #{q.question_id}</CardTitle>
                  {q.course_code && q.course_name && (
                    <p className="text-xs text-muted-foreground">
                      {q.course_code} – {q.course_name}
                    </p>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRemoveQuestion(q.question_id)}
                  className="flex items-center space-x-1"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Remove</span>
                </Button>
              </CardHeader>

              <CardContent>
                <p className="font-medium mb-2">{q.question_text}</p>
                {q.answer && (
                  <p className="text-sm text-muted-foreground mb-1">Answer: {q.answer}</p>
                )}
                {q.concepts && q.concepts.length > 0 && (
                  <p className="text-sm text-gray-700 mb-1">
                    Tags: {q.concepts.map((c) => c.trim()).join(", ")}
                  </p>
                )}
                {q.difficulty && (
                  <span
                    className={`inline-block px-2 py-1 text-xs rounded ${getDifficultyColor(
                      q.difficulty
                    )}`}
                  >
                    {q.difficulty}
                  </span>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
