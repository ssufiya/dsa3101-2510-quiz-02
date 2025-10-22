import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/card";
import { Input } from "../components/input";
import { Label } from "../components/label";
import { Button } from "../components/button";
import { Textarea } from "../components/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/select";
import {
  ArrowLeft,
  Save,
  HelpCircle,
  Plus,
  Trash2,
} from "lucide-react";
import { Badge } from "../components/badge";
import { toast } from "sonner";

export function EditQuestion({ questionId, questionData, onBack, onSave }) {
  // Initialize state from questionData prop
  const [questionText, setQuestionText] = useState(
    questionData?.question || ""
  );
  const initialOptions =
    questionData?.options ||
    (questionData?.type === "True/False" ? ["True", "False"] : ["", "", "", ""]);
  const [options, setOptions] = useState(initialOptions);
  const [correctAnswer, setCorrectAnswer] = useState(
    questionData?.correctAnswer !== undefined ? questionData.correctAnswer : 0
  );
  const [explanation, setExplanation] = useState(questionData?.explanation || "");
  const [courseName, setCourseName] = useState(questionData?.courseName || "");
  const [courseCode, setCourseCode] = useState(questionData?.courseCode || "");
  const [difficulty, setDifficulty] = useState(questionData?.difficulty || "Medium");
  const [questionType, setQuestionType] = useState(
    questionData?.type || "Multiple Choice"
  );
  const [tags, setTags] = useState(
    Array.isArray(questionData?.tags) ? questionData.tags.join(", ") : questionData?.tags || ""
  );

  const updateOption = (index, value) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const addOption = () => setOptions([...options, ""]);

  const removeOption = (index) => {
    if (options.length > 2) {
      const newOptions = options.filter((_, i) => i !== index);
      setOptions(newOptions);
      if (correctAnswer === index) setCorrectAnswer(0);
      else if (correctAnswer > index) setCorrectAnswer(correctAnswer - 1);
    }
  };

  const handleSave = () => {
    const baseData = {
      id: questionId,
      question: questionText,
      explanation,
      courseName,
      courseCode,
      difficulty,
      type: questionType,
      tags: tags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag !== ""),
      lastModified: new Date().toISOString(),
    };

    const updatedQuestion =
      questionType === "Multiple Choice" || questionType === "True/False"
        ? { ...baseData, options, correctAnswer }
        : baseData;

    if (onSave) {
      onSave(updatedQuestion);
      toast.success("Question updated successfully", {
        description: "Your changes have been saved.",
      });
    }
    onBack();
  };

  const isValid =
    questionText.trim() !== "" &&
    courseName.trim() !== "" &&
    courseCode.trim() !== "" &&
    (questionType === "Short Answer" ||
      questionType === "Essay" ||
      (questionType === "Multiple Choice" && options.every((opt) => opt.trim() !== "")) ||
      questionType === "True/False");

  if (!questionId || !questionData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="text-center p-8">
          <CardContent>
            <HelpCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg mb-2">Question Not Found</h3>
            <p className="text-muted-foreground mb-4">
              The requested question could not be found.
            </p>
            <Button onClick={onBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Question Details
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 space-x-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Question Details</span>
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
            <div className="flex items-center space-x-3">
              <div className="bg-primary rounded-lg p-2">
                <HelpCircle className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl">Edit Question</h1>
                <p className="text-sm text-muted-foreground">
                  Modify question details and content
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>Course and question metadata</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="courseCode">Course Code</Label>
                  <Input
                    id="courseCode"
                    placeholder="e.g., DSA1101"
                    value={courseCode}
                    onChange={(e) => setCourseCode(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="courseName">Course Name</Label>
                  <Input
                    id="courseName"
                    placeholder="e.g., Introduction to Data Science"
                    value={courseName}
                    onChange={(e) => setCourseName(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="difficulty">Difficulty</Label>
                  <Select value={difficulty} onValueChange={setDifficulty}>
                    <SelectTrigger id="difficulty" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="w-full whitespace-normal overflow-auto">
                      <SelectItem value="Easy">Easy</SelectItem>
                      <SelectItem value="Medium">Medium</SelectItem>
                      <SelectItem value="Hard">Hard</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="questionType">Question Type</Label>
                  <Select value={questionType} onValueChange={setQuestionType}>
                    <SelectTrigger id="questionType" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="w-full whitespace-normal overflow-auto">
                      <SelectItem value="Multiple Choice">Multiple Choice</SelectItem>
                      <SelectItem value="True/False">True/False</SelectItem>
                      <SelectItem value="Short Answer">Short Answer</SelectItem>
                      <SelectItem value="Essay">Essay</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  placeholder="e.g., Supervised Learning, Data Manipulation"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Separate tags with commas for better organization
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Question Content */}
          <Card>
            <CardHeader>
              <CardTitle>Question Content</CardTitle>
              <CardDescription>The main question and answer options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="question">Question</Label>
                <Textarea
                  id="question"
                  placeholder="Enter your question here"
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  rows={4}
                />
              </div>

              {/* Options Handling */}
              {questionType === "Multiple Choice" && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Label>Answer Options</Label>
                    <Button type="button" variant="outline" size="sm" onClick={addOption}>
                      <Plus className="h-3 w-3" /> Add Option
                    </Button>
                  </div>
                  {options.map((option, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="correct-answer"
                          checked={correctAnswer === index}
                          onChange={() => setCorrectAnswer(index)}
                        />
                        <span className="text-sm w-6">{String.fromCharCode(65 + index)}.</span>
                      </div>
                      <Input
                        placeholder={`Option ${String.fromCharCode(65 + index)}`}
                        value={option}
                        onChange={(e) => updateOption(index, e.target.value)}
                        className="flex-1"
                      />
                      {correctAnswer === index && (
                        <Badge className="bg-green-100 text-green-800">Correct</Badge>
                      )}
                      {options.length > 2 && (
                        <Button type="button" variant="ghost" size="sm" onClick={() => removeOption(index)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <p className="text-xs text-muted-foreground">
                    Select the radio button next to the correct answer
                  </p>
                </div>
              )}

              {questionType === "True/False" && (
                <div className="space-y-2">
                  <Label>Correct Answer</Label>
                  <div className="flex space-x-3">
                    <div className="flex items-center space-x-2">
                      <input type="radio" checked={correctAnswer === 0} onChange={() => setCorrectAnswer(0)} />
                      <span>True</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input type="radio" checked={correctAnswer === 1} onChange={() => setCorrectAnswer(1)} />
                      <span>False</span>
                    </div>
                  </div>
                </div>
              )}

              {(questionType === "Short Answer" || questionType === "Essay") && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    {questionType === "Short Answer"
                      ? "Short answer questions require manual grading."
                      : "Essay questions require manual grading."}
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="explanation">
                  {questionType === "Multiple Choice" || questionType === "True/False"
                    ? "Explanation (Optional)"
                    : "Grading Guidelines (Optional)"}
                </Label>
                <Textarea
                  id="explanation"
                  placeholder={
                    questionType === "Multiple Choice" || questionType === "True/False"
                      ? "Explain why this is the correct answer"
                      : "Provide guidelines for grading this answer"
                  }
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <Button variant="outline" onClick={onBack}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!isValid} className="flex items-center space-x-2">
              <Save className="h-4 w-4" />
              <span>Save Changes</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
