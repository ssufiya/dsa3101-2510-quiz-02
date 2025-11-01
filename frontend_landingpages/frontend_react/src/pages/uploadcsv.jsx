import { useState, useRef,  useEffect} from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/card";
import { Button } from "../components/button";
import { Upload, Download, Trash2, Save, ArrowLeft } from "lucide-react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../components/dialog";


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


  // ---- File Upload ----
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadStatus({ status: "uploading", message: "Uploading file..." });


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

      setUploadStatus({
      status: "success",
      message: response.data.error_message || "Preview loaded",
      has_duplicates: response.data.has_duplicates,
      duplicate_count: response.data.duplicate_count || 0
    })

    } catch (err) {
      console.error(err);
      setUploadStatus({ status: "error", message: err.message || "Upload failed" });
    }
  };

  //pop up notifs if duplicate questions
    useEffect(() => {
    if (uploadStatus.has_duplicates) {
      setShowDuplicateToast(true);
      const timer = setTimeout(() => setShowDuplicateToast(false), 8000); // auto-hide after 8s
       alert("Duplicated questions in uploaded file!");
      return () => clearTimeout(timer);
    }
  }, [uploadStatus]);

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
      <Card className="w-full">
        <CardHeader>
          <CardTitle>CSV Template Instructions</CardTitle>
          <CardDescription>Ensure your CSV/ZIP follows the format below:</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-700">
          <p className="font-semibold">Compulsory columns for Questions CSV:</p>
          <ul className="list-disc list-inside">
            <li>Context ID</li>
            <li>Question Number</li>
            <li>Question Text</li>
            <li>Question Type</li>
            <li>Correct Answer</li>
          </ul>
          <p className="font-semibold mt-2">Optional columns for Questions CSV:</p>
          <ul className="list-disc list-inside">
            <li>Sub-Question Number</li>
            <li>Option A–E</li>
            <li>Explanation</li>
            <li>Points</li>
            <li>Difficulty</li>
            <li>Concepts</li>
            <li>Attachment</li>
          </ul>
          <p className="font-semibold mt-2">Compulsory columns for Context CSV:</p>
          <ul className="list-disc list-inside">
            <li>Context ID</li>
            <li>Context Text</li>
          </ul>
        </CardContent>
      </Card>

      {/* Metadata Preview */}
      {metadata && (
        <Card className="mt-4 border-blue-400 w-full text-center">
          <CardHeader>
            <CardTitle>Metadata Preview</CardTitle>
            <CardDescription>
              Metadata extracted automatically from uploaded file name
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
      {questionsPreview.length > 0 && (
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Questions Preview ({questionsPreview.length})</CardTitle>
          </CardHeader>

          {uploadStatus.has_duplicates && (
            <div className="bg-red-100 border-l-4 border-red-600 text-red-800 p-3 mt-2 mb-2 rounded">
              <strong>⚠️ Duplicate questions detected!</strong>
              <p className="text-sm mt-1">Please review before confirming upload.</p>
              <ul className="list-disc list-inside text-sm mt-1">
                {uploadStatus.duplicate_indices?.map(i => (
                  <li key={i}>Q{i + 1}: {questionsPreview[i].question_text}</li>
                ))}
              </ul>
            </div>
          )}

          <CardContent className="space-y-4">
            {questionsPreview.map((q, i) => {
              const relatedContext = contextsPreview.find(c => c.context_id === q.context_id);
              const isDuplicate = uploadStatus.has_duplicates && uploadStatus.duplicate_indices?.includes(i);

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
