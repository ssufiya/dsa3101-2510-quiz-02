import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "../components/button";
import { Input } from "../components/input";
import { Textarea } from "../components/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/card";
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

  // --- Modal states ---
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
      setModalMessage("⚠️ Please fill in all required fields (Course Name, Course Code, Question Text).");
      setModalOpen(true);
      return;
    }

    const formattedDifficulty =
      difficulty.charAt(0).toUpperCase() + difficulty.slice(1).toLowerCase();

    const csvHeaders = [
      "question_text",
      "explanation",
      "course_name",
      "course_code",
      "assessment_type",
      "difficulty",
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
      points,
      `"${tags}"`,
      ...options.map((opt) => `"${opt.value.replace(/"/g, '""')}"`),
    ];

    const csvContent = csvHeaders.join(",") + "\n" + csvRow.join(",");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const formData = new FormData();
    formData.append("file", blob, `question_${questionId}_edit.csv`);

    try {
      const res = await axios.post(
        `http://localhost:5003/api/questions/${questionId}/editversion`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      console.log("✅ Upload response:", res.data);

      const newId = res.data.new_question_id;
      const newVersion = res.data.new_version_number;
      const parentId = res.data.previous_version_id || questionId;

      const newQuestionRes = await axios.get(`http://localhost:5003/api/questions/${newId}`);

      // Success modal
      setModalType("success");
      setModalMessage(`✅ Successfully uploaded!\nNew version: ${newVersion}`);
      setModalOpen(true);

      // Auto-close and return
      setTimeout(() => {
        setModalOpen(false);
        onSave(newQuestionRes.data, parentId);
      }, 2500);
    } catch (err) {
      console.error("❌ Error updating question:", err);

      const data = err.response?.data;
      let detail = "Error updating question.";

      if (typeof data === "string") detail = data;
      else if (Array.isArray(data?.errors)) detail = data.errors.join("\n• ");
      else if (typeof data?.detail === "string") detail = data.detail;
      else if (Array.isArray(data?.detail)) detail = data.detail.join("\n• ");
      else if (typeof data?.detail === "object" && data?.detail?.errors)
        detail = data.detail.errors.join("\n• ");

      setModalType("error");
      setModalMessage(`❌ Upload failed:\n${detail}`);
      setModalOpen(true);
    }
  };

  return (
    <>
      <Card className="p-4">
        <CardHeader>
          <CardTitle>Edit Question</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label>Course Name</label>
          <Input value={courseName} onChange={(e) => setCourseName(e.target.value)} />

          <label>Course Code</label>
          <Input value={courseCode} onChange={(e) => setCourseCode(e.target.value)} />

          <label>Difficulty</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="border rounded p-2 w-full"
          >
            {difficultyOptions.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>

          <label>Question Type</label>
          <select
            value={questionType}
            onChange={(e) => setQuestionType(e.target.value)}
            className="border rounded p-2 w-full"
          >
            {questionTypeOptions.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>

          <label>Assessment Type</label>
          <Input value={assessmentType} onChange={(e) => setAssessmentType(e.target.value)} />

          <label>Question Text</label>
          <Textarea value={questionText} onChange={(e) => setQuestionText(e.target.value)} />

          <label>Explanation</label>
          <Textarea value={explanation} onChange={(e) => setExplanation(e.target.value)} />

          <label>Points</label>
          <Input
            type="number"
            value={points}
            onChange={(e) => setPoints(Number(e.target.value))}
          />

          <label>Options</label>
          {options.map((opt, idx) => (
            <div key={idx} className="flex space-x-2 items-center">
              <span>{opt.key}.</span>
              <Input
                value={opt.value}
                onChange={(e) => handleOptionChange(idx, e.target.value)}
              />
            </div>
          ))}

          <label>Tags (comma separated)</label>
          <Input value={tags} onChange={(e) => setTags(e.target.value)} />

          <div className="flex space-x-2 mt-4">
            <Button onClick={handleSave}>Save / Upload New Version</Button>
            <Button variant="secondary" onClick={onBack}>Cancel</Button>
          </div>
        </CardContent>
      </Card>

      {/* --- Popup modal --- */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent
          className={`sm:max-w-md animate-fadeScale !text-white !border-none shadow-lg rounded-xl p-6 ${
            modalType === "success" ? "!bg-green-600" : "!bg-red-600"
          }`}
        >
          <DialogHeader>
            <DialogTitle className="text-white font-semibold">
              {modalType === "success" ? "Upload Successful" : "Upload Failed"}
            </DialogTitle>
            <DialogDescription className="text-white whitespace-pre-line">
              {modalMessage}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end pt-4">
            <Button
              variant="secondary"
              className="bg-white text-gray-800 hover:bg-gray-100"
              onClick={() => setModalOpen(false)}
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}