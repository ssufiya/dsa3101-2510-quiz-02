import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "../components/button";
import { Input } from "../components/input";
import { Textarea } from "../components/textarea";
import { Card, CardContent } from "../components/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../components/dialog";

export default function EditQuestion({ questionId, questionData, onBack, onSave }) {
  const [questionText, setQuestionText] = useState("");
  const [explanation, setExplanation] = useState("");
  const [courseName, setCourseName] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const [difficulty, setDifficulty] = useState("Med");
  const [questionType, setQuestionType] = useState("MCQ");
  const [assessmentType, setAssessmentType] = useState("");
  const [points, setPoints] = useState(1);
  const [options, setOptions] = useState([]);
  const [tags, setTags] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState("success");
  const [modalMessage, setModalMessage] = useState("");

  const difficultyOptions = ["Low", "Med", "High"];
  const questionTypeOptions = ["Code", "T/F", "MCQ", "MRQ", "SRQ"];

  useEffect(() => {
    if (questionData) {
      setQuestionText(questionData.question_text || "");
      setExplanation(questionData.explanation || "");
      setCourseName(questionData.course_name || "");
      setCourseCode(questionData.course_code || "");
      setDifficulty(questionData.difficulty || "Med");
      setQuestionType(questionData.question_type || "MCQ");
      setAssessmentType(questionData.assessment_type || "");
      setPoints(questionData.points || 1);
      if (questionData.options && typeof questionData.options === "object") {
        setOptions(
          Object.entries(questionData.options).map(([key, value]) => ({
            key,
            value,
          }))
        );
      }
      if (Array.isArray(questionData.concepts)) {
        setTags(questionData.concepts.join(", "));
      } else {
        setTags("");
      }
    }
  }, [questionData]);

  const handleOptionChange = (index, value) => {
    const updated = [...options];
    updated[index].value = value;
    setOptions(updated);
  };

  const handleSave = async () => {
    if (!questionText || !courseName || !courseCode) {
      setModalType("error");
      setModalMessage("Please ensure all required fields (Course Name, Course Code, Question Text) are filled.");
      setModalOpen(true);
      return;
    }

    const formattedDifficulty = difficulty.charAt(0).toUpperCase() + difficulty.slice(1).toLowerCase();

    const csvHeaders = [
      "question_text",
      "explanation",
      "course_name",
      "course_code",
      "assessment_type",
      "difficulty",
      "question_type",
      "points",
      "concepts",
      ...options.map((opt) => `option_${opt.key.toLowerCase()}`),
    ];

    const csvRow = [
      `"${questionText.replace(/"/g, '""')}"`,
      `"${explanation.replace(/"/g, '""')}"`,
      `"${courseName}"`,
      `"${courseCode}"`,
      `"${assessmentType}"`,
      `"${formattedDifficulty}"`,
      `"${questionType}"`,
      points,
      `"${tags}"`,
      ...options.map((opt) => `"${opt.value.replace(/"/g, '""')}"`),
    ];

    const csvContent = csvHeaders.join(",") + "\n" + csvRow.join(",");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const formData = new FormData();
    formData.append("file", blob, `question_${questionId}_edit.csv`);

    let uploadId = null;

    try {
      const previewRes = await axios.post(
        `http://localhost:5003/api/questions/edit?id=${questionId}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      uploadId = previewRes.data.upload_id;
      if (!uploadId) throw new Error("Please ensure either Course Code or Question Text is different.");

      const confirmRes = await axios.post("http://localhost:5003/api/questions/confirm-edits", {
        upload_id: uploadId,
      });

      if (confirmRes.data.success) {
        setModalType("success");
        setModalMessage("New version added successfully!");
      } else {
        throw new Error(confirmRes.data.message || "Confirm step failed");
      }

      setModalOpen(true);
      setTimeout(() => {
        setModalOpen(false);
        onSave({}, questionId);
      }, 2500);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Please ensure either Course Code or Question Text is different.";
      setModalType("error");
      setModalMessage(msg);
      setModalOpen(true);

      if (uploadId) {
        try {
          await axios.post("http://localhost:5003/api/questions/delete-edits", {
            upload_id: uploadId,
          });
          console.log(`🗑️ Cancelled failed upload ${uploadId}`);  // kept for debugging
        } catch (cancelErr) {
          console.warn("Failed to cancel upload:", cancelErr.message);  // kept for debugging
        }
      }
    }
  };

  const handleCancel = () => {
    setModalType("cancel");
    setModalMessage("Upload Cancelled");
    setModalOpen(true);
    setTimeout(() => {
      setModalOpen(false);
      onBack();
    }, 1500);
  };

  return (
    <>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "20px", marginTop: "10px" }}>
        <h1 style={{ fontSize: "32px", fontWeight: "600", color: "#111827" }}>Edit Question</h1>
        <p style={{ color: "#6b7280", fontSize: "14px" }}>
          Update the question details and save a new version
        </p>
      </div>

      {/* Form */}
      <Card style={{ padding: "16px" }}>
        <CardContent>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <label>Course Name</label>
            <Input value={courseName} onChange={(e) => setCourseName(e.target.value)} />

            <label>Course Code</label>
            <Input value={courseCode} onChange={(e) => setCourseCode(e.target.value)} />

            <label>Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={{ borderRadius: "6px", padding: "8px", border: "1px solid #ccc" }}
            >
              {difficultyOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>

            <label>Question Type</label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
              style={{ borderRadius: "6px", padding: "8px", border: "1px solid #ccc" }}
            >
              {questionTypeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>

            <label>Assessment Type</label>
            <Input value={assessmentType} onChange={(e) => setAssessmentType(e.target.value)} />

            <label>Question Text</label>
            <Textarea value={questionText} onChange={(e) => setQuestionText(e.target.value)} />

            <label>Explanation</label>
            <Textarea value={explanation} onChange={(e) => setExplanation(e.target.value)} />

            <label>Points</label>
            <Input type="number" value={points} onChange={(e) => setPoints(Number(e.target.value))} />

            <label>Options</label>
            {options.map((opt, idx) => (
              <div key={idx} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <span>{opt.key}.</span>
                <Input value={opt.value} onChange={(e) => handleOptionChange(idx, e.target.value)} />
              </div>
            ))}

            <label>Tags (comma separated)</label>
            <Input value={tags} onChange={(e) => setTags(e.target.value)} />

            <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
              <Button onClick={handleSave}>Save New Version</Button>
              <Button variant="secondary" onClick={handleCancel}>Cancel</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal */}
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
              backgroundColor:
                modalType === "success" ? "#16a34a" : "#dc2626", 
              color: "white",
              border:
                modalType === "success"
                  ? "4px solid #166534"
                  : "4px solid #991b1b",
              borderRadius: "16px",
              padding: "24px",
              boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <DialogHeader>
              <DialogTitle style={{ color: "white", fontWeight: "600" }}>
                {modalType === "success"
                  ? "Upload Successful"
                  : modalType === "cancel"
                  ? "Upload Cancelled"
                  : "Upload Failed"}
              </DialogTitle>
              <DialogDescription style={{ color: "white", whiteSpace: "pre-line" }}>
                {modalMessage}
              </DialogDescription>
            </DialogHeader>

            <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: "16px" }}>
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
    </>
  );
}