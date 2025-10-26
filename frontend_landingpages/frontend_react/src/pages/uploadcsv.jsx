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
  const [uploadedContexts, setUploadedContexts] = useState([]);
  const contextFileRef = useRef(null);
  const questionFileRef = useRef(null);


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
          row["Option_E"],
        ].filter((o) => o && o.trim() !== "");

        return {
          id: `preview-${idx + 1}`, // temporary id
          context_id:row["Context ID"] || "",
          question_number: row["Question Number"] || "",
          sub_question_number: row["Sub-Question Number"] || "",
          question_text: row["Question Text"] || "",
          question_type: row["Question_Type"] || "MCQ",
          options,
          correct_answer: row["Correct Answer"] || "",
          explanation: row["Explanation"] || "",
          points: row["Points"] || "",
          difficulty: row["Difficulty"] || "",
          concepts: row["Concepts"] || "",
          attachment: row["Attachment"] || "",
          course_code: courseCode,
          assessment_type: assessmentType,
          assessment_year: assessmentYear,
          assessment_semester: assessmentSemester
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

//parse context csv file 
const handleContextUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const contexts = results.data.map((row, idx) => ({
          id: `context-${idx + 1}`,
          context_id: row["Context ID"] || "",
          context_text: row["Context Text"] || "",
          attachment: row["Attachment"] || "",
        }));
        setUploadedContexts(contexts);
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
      { questions: uploadedQuestions,
        contexts:uploadedContexts,
      },
    );

    if (response.data.success) {
      setUploadStatus({ status: "success", message: response.data.message });
      setUploadedQuestions([]); // clear preview after save
      setUploadedContexts([]);
    }
  } catch (err) {
    setUploadStatus({ status: "error", message: err.message });
  }
};

//sample questions csv file 
const downloadSampleQuestionsCSV = () => {
    const sample = [
      "Context ID,Question Number,Sub-Question Number,Question Text,Question Type,Option A,Option B,Option C,Option D,Option E,Correct Answer,Explanation,Points,Difficulty,Concepts,Attachment",
      "1,1,,What is 2+2?,MCQ,3,4,5,6,,4,Simple arithmetic,1,Easy,Math,",
      "1,2,,The sky is blue.,True/False,,,,,,True,Basic knowledge,1,Easy,Science,"
    ].join("\n");
    const blob = new Blob([sample], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sample_questions.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

//sample context csv file
  const downloadSampleContextCSV = () => {
    const sample = [
      "Context ID,Context Text,Attachment",
      "1,This context provides background information for the questions above.,"
    ].join("\n");
    const blob = new Blob([sample], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sample_context.csv";
    a.click();
    URL.revokeObjectURL(url);
  };


const removeQuestion = (id) => setUploadedQuestions(prev => prev.filter(q => q.id !== id));
const removeContext = (id) => setUploadedContexts(prev => prev.filter(c => c.id !== id));
const getContextForQuestion = (questionNumber) => {
  return contexts.find(c => c.questionNumber.includes(questionNumber));
};


return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center h-16 space-x-4">
          <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Dashboard</span>
          </Button>
          <h1 className="text-xl font-semibold">Upload Questions & Contexts</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Assessment Info */}
        <Card>
          <CardHeader>
            <CardTitle>Assessment Information</CardTitle>
            <CardDescription>These fields apply to all uploaded questions</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Course Code *</Label>
              <Input value={courseCode} onChange={(e) => setCourseCode(e.target.value)} placeholder="e.g. DSA3101" />
            </div>
            <div>
              <Label>Assessment Type *</Label>
              <Select value={assessmentType} onValueChange={setAssessmentType}>
                <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Final">Final</SelectItem>
                  <SelectItem value="Midterm">Midterm</SelectItem>
                  <SelectItem value="Quiz">Quiz</SelectItem>
                  <SelectItem value="Assignment">Assignment</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Assessment Year *</Label>
              <Input value={assessmentYear} onChange={(e) => setAssessmentYear(e.target.value)} placeholder="e.g. 2425" />
            </div>
            <div>
              <Label>Assessment Semester *</Label>
              <Select value={assessmentSemester} onValueChange={setAssessmentSemester}>
                <SelectTrigger><SelectValue placeholder="Select semester" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Semester 1">Semester 1</SelectItem>
                  <SelectItem value="Semester 2">Semester 2</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Upload Questions CSV */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Questions CSV</CardTitle>
            <CardDescription>Required columns: Context ID, Question Number, Sub-Question Number, Question Text, Question Type, Option A–E, Correct Answer, Explanation, Points, Difficulty, Concepts, Attachment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-center">
            <Button onClick={() => questionFileRef.current?.click()}><Upload className="h-4 w-4 mr-2" />Choose Questions CSV</Button>
            <Button variant="outline" onClick={downloadSampleQuestionsCSV}><Download className="h-4 w-4 mr-2" />Download Sample</Button>
            <input ref={questionFileRef} type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
          </CardContent>
        </Card>

        {/* Upload Context CSV */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Context CSV</CardTitle>
            <CardDescription>Required columns: Context ID, Context Text, Attachment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-center">
            <Button onClick={() => contextFileRef.current?.click()}><Upload className="h-4 w-4 mr-2" />Choose Context CSV</Button>
            <Button variant="outline" onClick={downloadSampleContextCSV}><Download className="h-4 w-4 mr-2" />Download Sample</Button>
            <input ref={contextFileRef} type="file" accept=".csv" className="hidden" onChange={handleContextUpload} />
          </CardContent>
        </Card>

        {/* Preview */}
        {uploadedQuestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Questions Preview ({uploadedQuestions.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
            {uploadedQuestions.map((q, i) => {
              // find the matching context using Context ID
              const relatedContext = uploadedContexts.find(
                (c) => c.context_id === q.context_id
              );

              return (
                <div key={q.id} className="border p-3 rounded bg-white space-y-2">
                  {/* 🟢 Context block (only if context exists) */}
                  {relatedContext && (
                    <div className="bg-gray-50 p-2 rounded flex justify-between">
                      <p className="text-sm text-gray-700">
                        <strong>Context {relatedContext.context_id}:</strong>{" "}
                        {relatedContext.context_text}
                      </p>

                      {/* If context has an attachment */}
                      {relatedContext.attachment && (
                        <div className="mt-1">
                          <img
                            src={relatedContext.attachment}
                            alt={`context-${relatedContext.context_id}`}
                            className="max-h-32 rounded"
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* 🟡 Question block */}
                  <div className="flex justify-between">
                    <div>
                      <p className = "text-center">
                        <strong>Q{i + 1}:</strong> {q.question_text}
                      </p>
                      <p className="text-sm text-gray-600 text-center">
                        Type: {q.question_type} | Difficulty: {q.difficulty}
                      </p>

                      {/* show options if available */}
                      {q.options?.length > 0 && (
                        <ul className="list-disc list-inside text-sm text-gray-700">
                          {q.options.map((opt, idx) => (
                            <li key={idx}>{opt}</li>
                          ))}
                        </ul>
                      )}

                      {/* show correct answer */}
                      {q.correct_answer && (
                        <p className="text-sm text-green-700 mt-1">
                          <strong>Answer:</strong> {q.correct_answer}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      onClick={() => removeQuestion(q.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              );
            })}

                        </CardContent>
                      </Card>
                    )}

        {uploadedContexts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Contexts Preview ({uploadedContexts.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadedContexts.map((c, i) => (
                <div key={c.id} className="border p-3 rounded bg-white">
                  <div className="flex justify-between">
                    <div>
                      <p><strong>Context {c.context_id}:</strong> {c.context_text}</p>
                    </div>
                    <Button variant="ghost" onClick={() => removeContext(c.id)}><Trash2 className="h-4 w-4 text-red-600" /></Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Save Button */}
        {(uploadedQuestions.length > 0 || uploadedContexts.length > 0) && (
          <div className="flex justify-end">
            <Button onClick={handleSaveQuestions}><Save className="h-4 w-4 mr-2" />Save All</Button>
          </div>
        )}
      </div>
    </div>
  );
}