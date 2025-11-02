import { useState, useRef,  useEffect} from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/card";
import { Button } from "../components/button";
import { Upload, Download, Trash2, Save, ArrowLeft } from "lucide-react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../components/dialog";


console.log("UploadCSV component file loaded");

export function UploadCSV({ onBack }) {
  const [uploadStatus, setUploadStatus] = useState({ status: "idle" });
  const [questionsPreview, setQuestionsPreview] = useState([]);
  const [contextsPreview, setContextsPreview] = useState([]);
  const [uploadId, setUploadId] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const fileRef = useRef(null);
  const [showDuplicateToast, setShowDuplicateToast] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState("success"); // "success" | "error"
  const [modalMessage, setModalMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  // ---- File Upload ----
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadStatus({ status: "uploading", message: "Uploading file..." });
    setErrorMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        "http://localhost:5003/api/questions/upload",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setQuestionsPreview(response.data.questions || []);
      setContextsPreview(response.data.contexts || []);
      setUploadId(response.data.upload_id);
      

      // automatically extract metadata from backend response
      setMetadata({
        course_code: response.data.course_code,
        assessment_type: response.data.assessment_type,
        academic_year: response.data.academic_year,
        semester: response.data.semester,
      });

      //if duplicates found - show message
      if (response.data.has_duplicates) {
        setErrorMessage(
          response.data.error_message ||
            "Duplicate questions were found in your upload."
        );
      }


      setUploadStatus({
      status: "success",
      message:
        response.data.error_message && !response.data.has_duplicates
          ? response.data.error_message
          : "Preview loaded",
      has_duplicates: response.data.has_duplicates,
      duplicate_count: response.data.duplicate_count || 0,
    });

    } catch (err) {
      console.error("❌ Upload failed:", err);
      const backendError = err.response?.data?.detail || err.message || "Upload failed.";
      setErrorMessage(backendError);
      setUploadStatus({ status: "error", message: backendError });
    }
  };

  // ---- Confirm Upload ----
  const handleConfirmUpload = async () => {
    if (!uploadId) {
      alert("No uploaded file to confirm!");
      return;
    }

    setUploadStatus({ status: "saving", message: "Confirming upload..." });
  


    try {
      const payload = { upload_id: uploadId, metadata };

      const response = await axios.post(
        "http://localhost:5003/api/questions/confirm-upload",
        payload,
        { headers: { "Content-Type": "application/json" } }
      );

      setUploadStatus({ status: "success", message: response.data.message });
      setModalType("success");
      setModalType("success");
      setModalMessage(response.data.message || "Upload confirmed successfully!");
      setModalOpen(true);

      setQuestionsPreview([]);
      setContextsPreview([]);
      setUploadId(null);
      setMetadata(null);
    } catch (err) {
      console.error(err);
      setUploadStatus({ status: "error", message: err.message || "Upload confirmation failed" });
    }
  };

  const removeQuestion = (index) =>
    setQuestionsPreview((prev) => prev.filter((_, i) => i !== index));
  const removeContext = (index) =>
    setContextsPreview((prev) => prev.filter((_, i) => i !== index));

  // ---- Sample CSV Download ----
  const downloadQuizTemplate = () => {
  const url = "http://localhost:5003/api/questions/download";
  const a = document.createElement("a");
  a.href = url;
  a.download = "quiz_upload_template.zip";
  a.click();
};


  return (
  <div className="min-h-screen bg-gray-50 flex flex-col items-center">
    {/* Header */}
    <header className="bg-white border-b border-gray-200 w-full">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center h-16 space-x-4">
        <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Button>
        <h1 className="text-xl font-semibold">Upload Questions & Contexts</h1>
      </div>
    </header>

    {/* Main content */}
    <div className="w-full max-w-3xl px-4 py-8 space-y-8 flex flex-col items-center text-center">
      {/* Instructions */}
    <Card className="w-full text-center">
      <CardHeader>
        <CardTitle>📘 QuizBank Upload Summary</CardTitle>
        <CardDescription>
          Follow these key steps before uploading. You can also download the full template below.
        </CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-gray-700 space-y-3 text-center">
        <p><strong>1️⃣ Upload Format</strong></p>
        <ul className="list-disc list-inside ml-4">
          <li><strong>Single questions.csv</strong> – for uploads without shared contexts or attachments.</li>
          <li><strong>ZIP package</strong> – must include <code>questions.csv</code>; can also include <code>context.csv</code> and an <code>attachments/</code> folder.</li>
        </ul>

        <p><strong>2️⃣ File Naming</strong></p>
        <p>Use: <code>COURSECODE_SemX_YYYY_AssessmentTitle_[questions|context].csv</code><br/>
        Example: <code>DSA1101_Sem1_2425_Finals_questions.csv</code></p>

        <p><strong>3️⃣ When to Include context.csv</strong></p>
        <p>Add only if multiple questions share the same background text or dataset. Each context must have a unique <code>context_id</code>.</p>

        <p><strong>4️⃣ Attachments</strong></p>
        <ul className="list-disc list-inside ml-4">
          <li>Put all files in an <code>attachments/</code> folder inside the ZIP.</li>
          <li>Reference exact filenames in the <code>attachments</code> column.</li>
          <li>Supported: images (.png, .jpg), docs (.pdf, .docx), data/code (.csv, .py, .r), etc.</li>
        </ul>

        <p><strong>5️⃣ Upload Steps</strong></p>
        <ul className="list-decimal list-inside ml-4">
          <li>Prepare <code>questions.csv</code> (and <code>context.csv</code> if needed).</li>
          <li>Add any attachments.</li>
          <li>ZIP everything if contexts or attachments exist.</li>
          <li>Upload below — QuizBank will validate your file and show any errors.</li>
        </ul>

        <p className="mt-2 text-gray-600 italic">
          📥 For detailed column descriptions, download the full <strong>Quiz Template</strong> below.
        </p>
      </CardContent>
    </Card>


      {/* Metadata Preview */}
      {metadata && (
        <Card className="mt-4 border-blue-400 w-full text-center">
          <CardHeader>
            <CardTitle>Metadata Preview</CardTitle>
            <CardDescription>
              Ensure metadata is correct.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
            <div><strong>Course Code:</strong> {metadata.course_code || "-"}</div>
            <div><strong>Assessment Type:</strong> {metadata.assessment_type || "-"}</div>
            <div><strong>Assessment Year:</strong> {metadata.academic_year || "-"}</div>
            <div><strong>Assessment Semester:</strong> {metadata.semester || "-"}</div>
          </CardContent>
        </Card>
      )}

      {/* Upload CSV / ZIP */}
      <Card className="w-full text-center">
        <CardHeader>
          <CardTitle>Upload Questions CSV or ZIP</CardTitle>
          <CardDescription>Choose your CSV or ZIP file to preview questions and contexts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-center">
          <Button onClick={() => fileRef.current?.click()} className="mx-auto">
            <Upload className="h-4 w-4 mr-2" />Choose File
          </Button>
          <input ref={fileRef} type="file" accept=".csv,.zip" className="hidden" onChange={handleFileUpload} />
          <Button variant="outline" onClick={downloadQuizTemplate} className="mx-auto">
            <Download className="h-4 w-4 mr-2" /> Download Quiz Template
          </Button>
        </CardContent>
      </Card>

      {/* Questions Preview */}
      {errorMessage && (
        <div className="bg-red-50 border-2 border-red-600 text-red-800 rounded-xl p-4 my-3 shadow-md">
          <div className="flex items-center space-x-3 mb-2">
            <div className="bg-red-600 text-white rounded-full w-7 h-7 flex items-center justify-center font-bold">
              !
            </div>
            <h2 className="text-red-800 font-semibold text-lg">Upload Error</h2>
          </div>
          <p className="text-sm whitespace-pre-line">{errorMessage}</p>
        </div>
      )}

      {questionsPreview.length > 0 && (
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Questions Preview ({questionsPreview.length})</CardTitle>
            <li>Ensure that questions are correct before confirming upload. Otherwise, make edits to your files again.</li>
          </CardHeader>

          {uploadStatus.has_duplicates && (
            <div className="bg-red-100 border-l-4 border-red-600 text-red-800 p-3 mt-2 mb-2 rounded text-left">
              <strong>⚠️ Duplicate questions detected!</strong>
              <p className="text-sm mt-1">
                Some questions in your upload already exist in the system.  
                Please review your file and remove the duplicates before confirming upload.
              </p>
            </div>
          )}


          <CardContent className="space-y-4">
            {questionsPreview.map((q, i) => {
              const relatedContext = contextsPreview.find(c => c.context_id === q.context_id);
              const isDuplicate = uploadStatus.has_duplicates;

              return (
                <div key={i} className={`border p-3 rounded bg-white space-y-2 ${isDuplicate ? 'border-red-600 bg-red-50' : ''}`}>
                  {relatedContext && (
                    <div className="bg-gray-50 p-2 rounded text-center">
                      <p className="text-sm text-gray-700">
                        <strong>Context {relatedContext.context_id}:</strong> {relatedContext.context_text}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <p><strong>Q{i + 1}:</strong> {q.question_text}</p>
                     <p className="text-sm text-gray-600">Type: {q.question_type} | Difficulty: {q.difficulty}</p>
                    {q.options?.length > 0 && (
                      <ul className="list-disc list-inside text-sm">
                        {q.options.map((opt, idx) => <li key={idx}>{opt}</li>)}
                      </ul>
                    )}
                    {q.correct_answer && <p className="text-sm text-green-700">Answer: {q.correct_answer}</p>}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Confirm Upload Button */}
      {(questionsPreview.length > 0 || contextsPreview.length > 0) && (
        <div className="flex justify-center mt-4">
          <Button onClick={handleConfirmUpload}
            disabled={uploadStatus.has_duplicates || !uploadId}
            title={uploadStatus.has_duplicates ? "Resolve duplicates before confirming" : ""}
          >
            <Save className="h-4 w-4 mr-2" /> Confirm Upload
          </Button>
        </div>
      )}

      {/* Status */}
      {uploadStatus.status !== "idle" && (
        <p className={`mt-2 text-sm ${uploadStatus.status === "error" ? "text-red-600" : "text-green-700"} text-center`}>
          {uploadStatus.message}
        </p>
      )}
    </div>

    {/* --- Popup modal --- */}
    <Dialog open={modalOpen} onOpenChange={setModalOpen}>
      <DialogContent
        style={{
          backgroundColor: "transparent",
          border: "none",
          boxShadow: "none",
          padding: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "500px",
            height: "300px",
            backgroundColor: modalType === "success" ? "#16a34a" : "#dc2626",
            color: "white",
            border: `4px solid ${modalType === "success" ? "#166534" : "#991b1b"}`,
            borderRadius: "16px",
            padding: "24px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            alignItems: "center",
            textAlign: "center",
          }}
        >
          <DialogHeader>
            <DialogTitle style={{ color: "white", fontWeight: "600" }}>
              {modalType === "success" ? "Upload Successful" : "Upload Failed"}
            </DialogTitle>
            <DialogDescription style={{ color: "white", whiteSpace: "pre-line" }}>
              {modalMessage}
            </DialogDescription>
          </DialogHeader>

          <div style={{ display: "flex", justifyContent: "center", paddingTop: "16px" }}>
            <Button
              variant="secondary"
              style={{
                backgroundColor: "white",
                color: "#333",
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "8px 16px",
                cursor: "pointer",
              }}
              onClick={() => setModalOpen(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
);

}
