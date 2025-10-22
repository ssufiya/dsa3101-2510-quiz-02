import { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/card';
import { Button } from '../components/button';
import { Badge } from '../components/badge';
import { Progress } from '../components/progress';
import { Alert, AlertDescription } from '../components/alert';
import { 
  ArrowLeft, Upload, FileText, CheckCircle, AlertCircle, 
  Download, Trash2, Save
} from 'lucide-react';
import axios from 'axios';
import { Label } from "../components/label";
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "../components/select";
import { Input } from "../components/input";
import Papa from "papaparse";

//creates internal variable for the component instance

export function UploadCSV({ onBack }) {

  const [uploadStatus, setUploadStatus] = useState({ status: "idle" });
  const [uploadedQuestions, setUploadedQuestions] = useState([]);
  const fileInputRef = useRef(null);

  //manual inputs 
  const [courseCode, setCourseCode] = useState("");
  const [assessmentType, setAssessmentType] = useState("");
  const [assessmentYear, setAssessmentYear] = useState("");
  const [assessmentSemester, setAssessmentSemester] = useState("");

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
  
  //pre-parser to display question preview before passing to backend
const handleFileUpload = (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".csv")) {
    setUploadStatus({ status: "error", message: "Only CSV files allowed" });
    return;
  }

  setUploadStatus({ status: "parsing", progress: 0 });

  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      const questions = results.data.map((row, idx) => {
        const options = [
          row["Option A"],
          row["Option B"],
          row["Option C"],
          row["Option D"],
          row["Option E"],
        ].filter((o) => o && o.trim() !== "");

        return {
          id: `preview-${idx + 1}`, // temporary id
          question_text: row["Question Text"] || "",
          question_type: row["Question Type"] || "MCQ",
          options,
          answer: row["Correct Answer"] || "",
          difficulty: row["Difficulty"] || "",
          concepts: row["Concepts"] || "",
          marks: row["Points"] || 1,
          course_id: row["Course ID"] || "",
          assessment_id: row["Assessment ID"] || "",
          explanation: row["Explanation"] || "",
        };
      });

      setUploadedQuestions(questions);
      setUploadStatus({ status: "success", message: `${questions.length} questions parsed` });
    },
    error: (err) => {
      setUploadStatus({ status: "error", message: err.message });
    },
  });
};

//once questions are confirmed, questions will be sent to backend
const handleSaveQuestions = async () => {
  try {
    setUploadStatus({ status: "saving", progress: 0 });

    const response = await axios.post(
      "http://localhost:5001/api/questions/upload",
      { questions: uploadedQuestions },
    );

    if (response.data.success) {
      setUploadStatus({ status: "success", message: response.data.message });
      setUploadedQuestions([]); // clear preview after save
    }
  } catch (err) {
    setUploadStatus({ status: "error", message: err.message });
  }
};

//sample csv file 
  const downloadSampleCSV = () => {
  const sampleData = [
    // Headers: required first, then optional
    "question_text,question_type,difficulty,concepts,course_id,assessment_id,option_a,option_b,option_c,option_d,option_e,correct_answer",
    
    // Sample rows
    '"What is the capital of France?","MCQ","Easy","Geography",1,1,"Paris","London","Berlin","Madrid","","Paris"',
    '"Python is a programming language","Open-ended","Easy","Programming",2,1,"","","","","",""',
    '"What is 2 + 2?","MCQ","Easy","Math",3,1,"3","4","5","6","","4"',
  ].join("\n");

  const blob = new Blob([sampleData], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sample_questions.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const removeQuestion = (questionId) => {
  setUploadedQuestions((prev) => prev.filter((q) => q.id !== questionId));
};

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
              <span>Back to Dashboard</span>
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
            <h1 className="text-xl">Upload Questions from CSV</h1>
          </div>
        </div>
      </header>

    {/* main content wrapper */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
       
        {/* Manual Input Fields Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Assessment Information</CardTitle>
            <CardDescription>
              Enter the course and assessment details that will be applied to all uploaded questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="courseCode">Course Code *</Label>
                <Input
                  id="courseCode"
                  placeholder="e.g., CS201"
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="assessmentType">Assessment Type *</Label>
                <Select value={assessmentType} onValueChange={setAssessmentType}>
                  <SelectTrigger id="assessmentType">
                    <SelectValue placeholder="Select assessment type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Final">Final Exam</SelectItem>
                    <SelectItem value="Midterm">Midterm Exam</SelectItem>
                    <SelectItem value="Quiz">Quiz</SelectItem>
                    <SelectItem value="Assignment">Assignment</SelectItem>
                    <SelectItem value="Practice">Practice Test</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="assessmentYear">Assessment Year *</Label>
                <Input
                  id="assessmentYear"
                  placeholder="e.g., AY23/24 or 2024"
                  value={assessmentYear}
                  onChange={(e) => setAssessmentYear(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="assessmentSemester">Assessment Semester *</Label>
                <Select value={assessmentSemester} onValueChange={setAssessmentSemester}>
                  <SelectTrigger id="assessmentSemester">
                    <SelectValue placeholder="Select semester" />
                  </SelectTrigger>
                  <SelectContent className="bg-white text-black" position="popper">
                    <SelectItem value="Semester 1">Semester 1</SelectItem>
                    <SelectItem value="Semester 2">Semester 2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <Alert className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                These fields are required and will be automatically applied to all questions uploaded from the CSV file.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* CSV Upload Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Upload className="h-5 w-5" />
              <span>Import Questions from CSV File</span>
            </CardTitle>
            <CardDescription>
              Import questions in bulk from a CSV file to quickly build your question library
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {uploadStatus.status === "idle" && (
              <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="mb-2">Drop your CSV file here or click to browse</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Supported format: CSV files with question, options, course info, and difficulty
                </p>
                <div className="flex justify-center space-x-3">
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center space-x-2"
                  >
                    <Upload className="h-4 w-4" />
                    <span>Choose File</span>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={downloadSampleCSV}
                    className="flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download Sample</span>
                  </Button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            )}

            {(uploadStatus.status === "uploading" || uploadStatus.status === "parsing") && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                  <span className="text-sm">
                    {uploadStatus.status === "uploading" ? "Reading file..." : "Processing questions..."}
                  </span>
                </div>
                <Progress value={uploadStatus.progress || 0} className="w-full" />
              </div>
            )}

            {uploadStatus.status === "success" && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  {uploadStatus.message}
                </AlertDescription>
              </Alert>
            )}

            {uploadStatus.status === "error" && (
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {uploadStatus.message}
                </AlertDescription>
              </Alert>
            )}

            <div className="text-xs text-muted-foreground bg-muted p-3 rounded">
              <strong>CSV Format Requirements:</strong>
              <br />
              Required columns: question_text, question_type(MCQ, Open-Ended etc.), difficulty, concepts, course_id, assessment_id
              <br />
              Optional: MCQ Options (Option A, Option B...) , Answer
            </div>
          </CardContent>
        </Card>

        {/* Question Preview Section */}

        {uploadedQuestions.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Upload Summary</CardTitle>
                  <CardDescription>
                    Overview of the questions successfully imported
                  </CardDescription>
                </div>
                <Badge variant="secondary">{uploadedQuestions.length} Questions</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">Total Questions</p>
                  <p className="text-2xl font-semibold text-blue-900">{uploadedQuestions.length}</p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">Courses</p>
                  <p className="text-2xl font-semibold text-green-900">
                    {[...new Set(uploadedQuestions.map(q => q.courseCode))].filter(Boolean).length}
                  </p>
                </div>

                <div className="p-4 bg-yellow-50 rounded-lg">
                  <p className="text-sm text-yellow-800">Difficulty Breakdown</p>
                  <ul className="text-sm text-yellow-900">
                    <li>Easy: {uploadedQuestions.filter(q => q.difficulty === "Easy").length}</li>
                    <li>Medium: {uploadedQuestions.filter(q => q.difficulty === "Medium").length}</li>
                    <li>Hard: {uploadedQuestions.filter(q => q.difficulty === "Hard").length}</li>
                  </ul>
                </div>
              </div>

              <div className="border-t pt-4 text-sm text-gray-700">
                <p>
                  ✅ All questions have been successfully uploaded to your question library.  
                  You can now view or edit them individually under <strong>Manage Questions</strong>.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      

        {/*question preview for more details*/}

     {/* Question Preview Section */}
        {uploadedQuestions.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>
                    Uploaded Questions Preview
                  </CardTitle>
                  <CardDescription>
                    Review and manage your uploaded questions
                    before using them in quizzes
                  </CardDescription>
                </div>
                <Badge variant="secondary">
                  {uploadedQuestions.length} Questions
                </Badge>
              </div>
              
              {/* Assessment Information Summary */}
              {(courseCode || assessmentType || assessmentYear || assessmentSemester) && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="text-sm mb-2 text-blue-900">Applied Assessment Information:</h4>
                  <div className="flex flex-wrap gap-2">
                    {courseCode && (
                      <Badge variant="secondary">Course: {courseCode}</Badge>
                    )}
                    {assessmentType && (
                      <Badge variant="secondary">Type: {assessmentType}</Badge>
                    )}
                    {assessmentYear && (
                      <Badge variant="secondary">Year: {assessmentYear}</Badge>
                    )}
                    {assessmentSemester && (
                      <Badge variant="secondary">Semester: {assessmentSemester}</Badge>
                    )}
                  </div>
                </div>
              )}
            </CardHeader>
            <CardContent>

              {/* Questions List */}
              <div className="space-y-4">
                {uploadedQuestions.map((question, qIndex) => (
                  <Card
                    key={question.id}
                    className="border-l-4 border-l-blue-500"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start gap-4">
                        <div className="flex-1">
                          <div className="flex items-start gap-2 mb-2">
                            <Badge variant="outline" className="text-xs">
                              Q{qIndex + 1}
                            </Badge>
                            <Badge variant="secondary">
                              {question.question_type}
                            </Badge>
                          </div>
                          <CardTitle className="text-base leading-relaxed">
                            {question.question_text}
                          </CardTitle>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            removeQuestion(question.id)
                          }
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 flex-shrink-0"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-4">
                      {/* Options for MCQ */}
                      {question.question_type === "MCQ" && question.options && question.options.length > 0 && (
                        <div>
                          <h4 className="text-sm mb-2 text-muted-foreground">Options:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {question.options.map(
                              (option, index) => (
                                <div
                                  key={index}
                                  className={`p-3 rounded text-sm border ${
                                    question.answer === option
                                      ? "bg-green-50 text-green-900 border-green-300 font-medium"
                                      : "bg-gray-50 border-gray-200"
                                  }`}
                                >
                                  <span className="font-medium mr-2">
                                    {String.fromCharCode(
                                      65 + index,
                                    )}.
                                  </span>
                                  {option}
                                  {question.answer === option && (
                                    <span className="ml-2 text-xs text-green-700">
                                      ✓ Correct Answer
                                    </span>
                                  )}
                                </div>
                              ),
                            )}
                          </div>
                        </div>
                      )}

                      {/* Correct Answer for True/False */}
                      {question.question_type === "True/False" && question.answer && (
                        <div>
                          <h4 className="text-sm mb-2 text-muted-foreground">Answer:</h4>
                          <div className="flex gap-3">
                            <div
                              className={`px-4 py-2 rounded text-sm border ${
                                question.answer === "True"
                                  ? "bg-green-50 text-green-900 border-green-300 font-medium"
                                  : "bg-gray-50 border-gray-200"
                              }`}
                            >
                              True
                              {question.answer === "True" && (
                                <span className="ml-2 text-xs text-green-700">
                                  ✓ Correct
                                </span>
                              )}
                            </div>
                            <div
                              className={`px-4 py-2 rounded text-sm border ${
                                question.answer === "False"
                                  ? "bg-green-50 text-green-900 border-green-300 font-medium"
                                  : "bg-gray-50 border-gray-200"
                              }`}
                            >
                              False
                              {question.answer === "False" && (
                                <span className="ml-2 text-xs text-green-700">
                                  ✓ Correct
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Answer for Open-Ended */}
                      {question.question_type === "Open-Ended" && question.answer && (
                        <div>
                          <h4 className="text-sm mb-2 text-muted-foreground">Expected Answer:</h4>
                          <div className="p-3 bg-green-50 border border-green-200 rounded text-sm">
                            {question.answer}
                          </div>
                        </div>
                      )}

                      {/* Explanation */}
                      {question.explanation && (
                        <div>
                          <h4 className="text-sm mb-2 text-muted-foreground">Explanation:</h4>
                          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                            {question.explanation}
                          </div>
                        </div>
                      )}

                      {/* Metadata Footer */}
                      <div className="pt-3 border-t">
                        <div className="flex flex-wrap gap-2 items-center">
                          <span className="text-xs text-muted-foreground mr-1">Metadata:</span>
                          {question.difficulty && (
                            <Badge
                              className={getDifficultyColor(
                                question.difficulty,
                              )}
                            >
                              Difficulty: {question.difficulty}
                            </Badge>
                          )}
                          {question.marks !== undefined && (
                            <Badge variant="outline" className="bg-amber-50">
                              {question.marks} {question.marks === 1 ? "mark" : "marks"}
                            </Badge>
                          )}
                          {question.concepts && (
                            <Badge variant="secondary" className="bg-purple-50 text-purple-800">
                              Topic: {question.concepts}
                            </Badge>
                          )}
                          {question.course_id && (
                            <Badge variant="secondary" className="bg-blue-50 text-blue-800">
                              Course: {question.course_id}
                            </Badge>
                          )}
                          {question.assessment_id && (
                            <Badge variant="secondary" className="bg-slate-50 text-slate-800">
                              Assessment: {question.assessment_id}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {uploadedQuestions.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">
                      No questions uploaded yet. Upload a CSV
                      file to see questions here.
                    </p>
                  </div>
                )}
              </div>

              {/* Save Questions Button */}
              {uploadedQuestions.length > 0 && (
                <div className="mt-6 flex justify-end space-x-3">
                  <Button
                    variant="outline"
                    onClick={() => setUploadedQuestions([])}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={handleSaveQuestions}
                    className="flex items-center space-x-2"
                  >
                    <Save className="h-4 w-4" />
                    <span>Save {uploadedQuestions.length} Questions to Library</span>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}