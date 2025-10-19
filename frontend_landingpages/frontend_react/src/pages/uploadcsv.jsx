import { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/card';
import { Button } from '../components/button';
import { Badge } from '../components/badge';
import { Progress } from '../components/progress';
import { Alert, AlertDescription } from '../components/alert';
import { 
  ArrowLeft, Upload, FileText, CheckCircle, AlertCircle, 
  Download, Trash2
} from 'lucide-react';
import axios from 'axios';

//creates internal variable for the component instance

export function UploadCSV({ onBack }) {

  const [uploadStatus, setUploadStatus] = useState({ status: "idle" });
  const [uploadedQuestions, setUploadedQuestions] = useState([]);
  const fileInputRef = useRef(null);

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
  
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    //error if not csv file
    if (!file.name.toLowerCase().endsWith(".csv") && !file.name.toLowerCase().endsWith(".zip")) {
      setUploadStatus({
        status: "error",
        message: "Please upload a CSV or ZIP file only.",
      });
      return;
    }

    setUploadStatus({ status: "uploading", progress: 0 });

    try {
    // Build FormData to send to backend
    const formData = new FormData();
    formData.append("file", file);

    ///

    // Send request to your backend
    const response = await axios.post("/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadStatus({ status: "uploading", progress });
      },
    });
    //check if progressEvent.Total is provided in the browser

    const data = response.data;
    setUploadStatus({
      status: "success",
      message: data.message || "File uploaded successfully!",
      progress: 100,
    });

    // show how many questions addedd
    if (data.questions_added) {
      setUploadedQuestions((prev) => [
        ...prev,
        { id: `upload-${Date.now()}`, text: `${data.questions_added} questions added` },
      ]);
    }

    setTimeout(() => {
      setUploadStatus({ status: "idle" });
    }, 3000);

    //handle error
  } catch (error) {
    console.error("Upload error:", error);
    const message =
      error.response?.data?.error ||
      error.message ||
      "Error uploading file. Please try again.";

    setUploadStatus({
      status: "error",
      message,
    });
  }
  
   if (fileInputRef.current) {
    fileInputRef.current.value = "";
  }
};

//sample csv file 
  const downloadSampleCSV = () => {
    const sampleData = [
      "question,option_a,option_b,option_c,option_d,correct_answer,difficulty,course_name,course_code,type,tags",
      '"What is the capital of France?","Paris","London","Berlin","Madrid",0,Easy,"Introduction to Geography","GEOG101","Multiple Choice","geography;europe"',
      '"Python is a programming language","True","False","","",0,Easy,"Computer Science Fundamentals","CS101","True/False","programming;python"',
      '"What is 2 + 2?","3","4","5","6",1,Easy,"Basic Mathematics","MATH101","Multiple Choice","arithmetic;basics"',
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
              Required columns: question, option_a, option_b, option_c, option_d, correct_answer (0-3),
              difficulty (Easy/Medium/Hard), course_name, course_code, type (Multiple Choice/True/False/Short Answer)
              <br />
              Optional: tags (semicolon-separated)
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

        {/*{uploadedQuestions.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Uploaded Questions Preview</CardTitle>
                  <CardDescription>
                    Review and manage your uploaded questions before using them in quizzes
                  </CardDescription>
                </div>
                <Badge variant="secondary">{uploadedQuestions.length} Questions</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {uploadedQuestions.map((question) => (
                  <Card key={question.id} className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <CardTitle className="text-base">{question.text}</CardTitle>
                          <CardDescription className="mt-1">
                            {question.courseCode} - {question.courseName}
                          </CardDescription>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getDifficultyColor(question.difficulty)}>
                            {question.difficulty}
                          </Badge>
                          <Badge variant="outline">{question.type}</Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeQuestion(question.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      {question.type === "Multiple Choice" && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {question.options.map((option, index) => (
                            <div
                              key={index}
                              className={`p-2 rounded text-sm ${
                                index === question.correctAnswer
                                  ? "bg-green-100 text-green-800 border border-green-300"
                                  : "bg-gray-50"
                              }`}
                            >
                              <span className="font-medium">
                                {String.fromCharCode(65 + index)}.
                              </span>{" "}
                              {option}
                              {index === question.correctAnswer && (
                                <span className="ml-2 text-xs">✓ Correct</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {question.type === "True/False" && (
                        <div className="flex space-x-4">
                          <div
                            className={`p-2 rounded text-sm ${
                              question.correctAnswer === 0
                                ? "bg-green-100 text-green-800 border border-green-300"
                                : "bg-gray-50"
                            }`}
                          >
                            True{" "}
                            {question.correctAnswer === 0 && (
                              <span className="ml-2 text-xs">✓ Correct</span>
                            )}
                          </div>
                          <div
                            className={`p-2 rounded text-sm ${
                              question.correctAnswer === 1
                                ? "bg-green-100 text-green-800 border border-green-300"
                                : "bg-gray-50"
                            }`}
                          >
                            False{" "}
                            {question.correctAnswer === 1 && (
                              <span className="ml-2 text-xs">✓ Correct</span>
                            )}
                          </div>
                        </div>
                      )}

                      {question.tags && question.tags.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1">
                          {question.tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card> */}
      </div>
    </div>
  );
}
