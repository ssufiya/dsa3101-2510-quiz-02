import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "../components/button";
import { Input } from "../components/input";
import { Textarea } from "../components/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/card";

export default function EditQuestion({ questionId, questionData, onBack, onSave }) {
  const [questionText, setQuestionText] = useState("");
  const [explanation, setExplanation] = useState("");
  const [courseName, setCourseName] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const [difficulty, setDifficulty] = useState("Medium");
  const [questionType, setQuestionType] = useState("Multiple Choice");
  const [assessmentType, setAssessmentType] = useState("");
  const [points, setPoints] = useState(1);
  const [options, setOptions] = useState([]);
  const [tags, setTags] = useState("");

  const difficultyOptions = ["low", "med", "hard"];
  const questionTypeOptions = ["Code", "T/F", "MCQ", "MRQ","SRQ"];

  useEffect(() => {
    if (questionData) {
      setQuestionText(questionData.question_text || "");
      setExplanation(questionData.explanation || "");
      setCourseName(questionData.course_name || "");
      setCourseCode(questionData.course_code || "");
      setDifficulty(questionData.difficulty || "Medium");
      setQuestionType(questionData.question_type || "Multiple Choice");
      setAssessmentType(questionData.assessment_type || "");
      setPoints(questionData.points || 1);

      if (questionData.options && typeof questionData.options === "object") {
        setOptions(
          Object.entries(questionData.options).map(([key, value]) => ({ key, value }))
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
    if (!questionText) return alert("Question text required");

    const csvHeaders = [
      "question_text",
      "explanation",
      "course_code",
      "assessment_type",
      "difficulty",
      "points",
      "concepts",
      ...options.map((opt) => `option_${opt.key.toLowerCase()}`)
    ];

    const csvRow = [
      `"${questionText.replace(/"/g, '""')}"`,
      `"${explanation.replace(/"/g, '""')}"`,
      `"${courseCode}"`,
      `"${assessmentType}"`,
      `"${difficulty}"`,
      points,
      `"${tags}"`,
      ...options.map((opt) => `"${opt.value.replace(/"/g, '""')}"`)
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

      const newId = res.data.new_question_id;
      const newQuestionRes = await axios.get(
        `http://localhost:5003/api/questions/${newId}`
      );

      alert(`✅ Question updated! New version: ${res.data.new_version_number}`);
      onSave(newQuestionRes.data);
      onBack();
    } catch (err) {
      console.error("❌ Error updating question:", err);
      alert(err.response?.data?.detail || "Error updating question");
    }
  };

  return (
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
  );
}