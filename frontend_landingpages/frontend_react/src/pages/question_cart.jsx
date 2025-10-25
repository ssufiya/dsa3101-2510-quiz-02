import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { ArrowLeft, Trash2 } from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function QuestionCart({
  onBack,
  onBackToLibrary,
  onBackToDetails,
  selectedQuestionId, 
  questions,
  onRemoveQuestion,
}) {
  const [localQuestions, setLocalQuestions] = useState([]);

  useEffect(() => {
    // Sync cart questions from props
    setLocalQuestions(questions || []);
  }, [questions]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case "low":
      case "easy":
        return "bg-green-100 text-green-800";
      case "med":
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // 📄 Export as PDF
  const handleExportPDF = () => {
    console.log("Exporting PDF...");
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4",
    });

    if (localQuestions.length === 0) {
      alert("No questions to export!");
      return;
    }

    // 🏫 Header
    const firstQuestion = localQuestions[0];
    const courseCode = firstQuestion.course_code || "N/A";
    const courseName = firstQuestion.course_name || "N/A";

    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text("National University of Singapore", 105, 15, { align: "center" });

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    doc.text(`Course Code: ${courseCode}`, 14, 30);
    doc.text(`Course Name: ${courseName}`, 14, 38);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text("Question Paper", 14, 50);

    // ✏️ Start listing questions
    let yPosition = 65;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);

    localQuestions.forEach((q, index) => {
      let questionText = `${index + 1}. ${q.question_text || "N/A"}`;
      const questionType = q.question_type?.toLowerCase() || "short";

      // For True/False questions
      if (questionType === "truefalse" || questionType === "true/false") {
        questionText += "  (True / False)";
      }

      // Wrap question text
      const splitText = doc.splitTextToSize(questionText, 180);
      doc.text(splitText, 14, yPosition);
      yPosition += splitText.length * 7;

      // Add MCQ options if available
      if (questionType === "mcq" && q.options?.length > 0) {
        q.options.forEach((option, i) => {
          const optionLabel = String.fromCharCode(65 + i); // A, B, C, D...
          const optionText = `${optionLabel}. ${option}`;
          const splitOption = doc.splitTextToSize(optionText, 170);
          doc.text(splitOption, 20, yPosition);
          yPosition += splitOption.length * 6;
        });
      }

      // Add some spacing before next question
      yPosition += 6;

      // Add a new page if reaching the bottom
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }
    });

    // 💾 Save file
    const filename = `${courseCode}_question_paper.pdf`;
    doc.save(filename);
  };

  // 🧭 Smart back button handler
  const handleBackToQuestion = () => {
    if (selectedQuestionId && onBackToDetails) {
      onBackToDetails();
    } else if (onBackToLibrary) {
      onBackToLibrary();
    } else if (onBack) {
      onBack();
    }
  };

  return (
    <div className="p-6 space-y-4 min-h-screen bg-gray-50">
      {/* Navigation Buttons */}
      <div className="flex space-x-2">
        {/* Back to Dashboard */}
        <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Button>

        {/* Back to Library */}
        {onBackToLibrary && (
          <Button
            variant="ghost"
            onClick={onBackToLibrary}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Library</span>
          </Button>
        )}

        {/* Back to Question — only shown if a question is selected */}
        {onBackToDetails && selectedQuestionId && (
          <Button
            variant="ghost"
            onClick={handleBackToQuestion}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Question</span>
          </Button>
        )}
      </div>

      <h2 className="text-xl font-bold mt-4">Preview Selected Questions</h2>

      {localQuestions.length === 0 ? (
        <p className="text-gray-500 mt-4">No questions in your cart yet.</p>
      ) : (
        <div className="grid gap-4 mt-4">
          {localQuestions.map((q) => (
            <Card key={q.question_id} className="shadow-sm">
              <CardHeader className="flex justify-between items-center">
                <div className="flex flex-col">
                  <CardTitle className="text-sm">Question #{q.question_id}</CardTitle>
                  {q.course_code && q.course_name && (
                    <p className="text-xs text-muted-foreground">
                      {q.course_code} – {q.course_name}
                    </p>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRemoveQuestion(q.question_id)}
                  className="flex items-center space-x-1"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Remove</span>
                </Button>
              </CardHeader>

              <CardContent>
                <p className="font-medium mb-2">{q.question_text}</p>
                {q.answer && (
                  <p className="text-sm text-muted-foreground mb-1">
                    Answer: {q.answer}
                  </p>
                )}
                {q.concepts && q.concepts.length > 0 && (
                  <p className="text-sm text-gray-700 mb-1">
                    Tags: {q.concepts.map((c) => c.trim()).join(", ")}
                  </p>
                )}
                {q.difficulty && (
                  <span
                    className={`inline-block px-2 py-1 text-xs rounded ${getDifficultyColor(
                      q.difficulty
                    )}`}
                  >
                    {q.difficulty}
                  </span>
                )}
              </CardContent>
            </Card>
          ))}

          {/* Export Button */}
          <button
            onClick={handleExportPDF}
            className="mt-2 bg-blue-600 text-white px-3 py-2 rounded"
          >
            Export to PDF
          </button>
        </div>
      )}
    </div>
  );
}
