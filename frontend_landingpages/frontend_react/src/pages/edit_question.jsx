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

  useEffect(() => {
    if (questionData) {
      console.log("🟩 Populating fields with:", questionData);

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
    try {
      const payload = {
        question_text: questionText,
        explanation,
        course_name: courseName,
        course_code: courseCode,
        difficulty,
        question_type: questionType,
        assessment_type: assessmentType,
        points,
        options: options.reduce((acc, { key, value }) => {
          acc[key] = value;
          return acc;
        }, {}),
        concepts: tags.split(",").map((t) => t.trim()),
      };

      const res = await axios.put(
        `http://localhost:5003/api/questions/${questionId}`,
        payload
      );

      alert("✅ Question updated successfully!");
      onSave(res.data);
      onBack();
    } catch (err) {
      console.error("❌ Error updating question:", err);
      alert("Error updating question");
    }
  };

  return (
    <Card className="p-4">
      <CardHeader>
        <CardTitle>Edit Question</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <label>Course Name</label>
        <Input
          value={courseName}
          onChange={(e) => setCourseName(e.target.value)}
        />

        <label>Course Code</label>
        <Input
          value={courseCode}
          onChange={(e) => setCourseCode(e.target.value)}
        />

        <label>Difficulty</label>
        <Input
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        />

        <label>Question Type</label>
        <Input
          value={questionType}
          onChange={(e) => setQuestionType(e.target.value)}
        />

        <label>Assessment Type</label>
        <Input
          value={assessmentType}
          onChange={(e) => setAssessmentType(e.target.value)}
        />

        <label>Question Text</label>
        <Textarea
          value={questionText}
          onChange={(e) => setQuestionText(e.target.value)}
        />

        <label>Explanation</label>
        <Textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
        />

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
        <Input
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />

        <div className="flex space-x-2 mt-4">
          <Button onClick={handleSave}>Save</Button>
          <Button variant="secondary" onClick={onBack}>
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}