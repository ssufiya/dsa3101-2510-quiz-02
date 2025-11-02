import { useEffect, useState } from "react";
import { Card, CardContent } from "../components/card";
import { Button } from "../components/button";
import { ArrowLeft, Trash2, Eye } from "lucide-react";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function QuestionCart({
  onBack,
  onBackToLibrary,
  onBackToDetails,
  selectedQuestionId,
  questions,
  onRemoveQuestion,
  fromDetailsPage,
}) {
  const [localQuestions, setLocalQuestions] = useState([]);
  const [assessmentName, setAssessmentName] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const [courseName, setCourseName] = useState("");

  const courseMap = {
    DSA1101: "Introduction to Data Science",
    DSA2101: "Essential Data Analytics Tools",
    DSA3101: "Data Science in Practice",
    DSA3361: "Computational Data Science",
    DSA3362: "Applied Data Science",
    DSA4211: "Statistical Learning I",
    DSA4212: "Statistical Learning II",
    DSA4213: "Data Visualisation",
    DSA4262: "Bayesian Statistics",
    DSA4263: "Time Series Analysis",
    DSA4264: "Network Data Analytics",
    DSA4265: "Optimization for Data Science",
    DSA4266: "Natural Language Processing",
    DSE1101: "Data Science Principles",
    DSE3101: "Advanced Data Science Practice",
    HS2914: "Statistics for Health Sciences",
    ST1131: "Introduction to Statistics",
    ST2131: "Probability",
    ST2132: "Mathematical Statistics",
    ST2137: "Regression and Analysis of Variance",
    ST2334: "Probability and Statistics",
    ST3131: "Regression Analysis",
    ST3232: "Design of Experiments",
    ST3236: "Sampling Theory and Methods",
    ST3239: "Applied Regression",
    ST3244: "Survey Methodology",
    ST3246: "Multivariate Analysis",
    ST3247: "Stochastic Processes I",
    ST3248: "Applied Machine Learning",
    ST4231: "Statistical Inference",
    ST4233: "Advanced Statistical Theory",
    ST4234: "Time Series Analysis II",
    ST4238: "Bayesian Data Analysis",
    ST4245: "Survival Analysis",
    ST4248: "Statistical Machine Learning",
    ST4250: "Nonparametric Statistics",
    ST4253: "Data Mining Techniques",
    DSS5101: "Fundamentals of Data Science",
    DSS5102: "Statistical Computing",
    DSS5103: "Statistical Inference for Data Science",
    DSS5104: "Machine Learning Methods",
    DSS5105: "Applied Analytics",
    DSS5201: "Data Visualisation and Communication",
    DSS5202: "Big Data Analytics",
    DSS5203: "Advanced Machine Learning",
    DSS5210: "Research Project I",
    DSS5211: "Research Project II",
    ST5201X: "Advanced Statistical Theory (Extended)",
    ST5202: "Probability Theory",
    ST5202X: "Probability Theory (Extended)",
    ST5203: "Linear Models",
    ST5209X: "Stochastic Processes II",
    ST5211X: "Statistical Computation",
    ST5188: "Graduate Research Seminar",
    ST5207: "Advanced Regression Analysis",
    ST5212: "Modern Multivariate Methods",
    ST5213: "Bayesian Computation",
    ST5218: "Deep Learning in Statistics",
    ST5221: "Statistical Genomics",
    ST5225: "Financial Time Series",
    ST5226: "Functional Data Analysis",
    ST5227: "Data Privacy and Ethics",
    ST5229: "Causal Inference",
    ST5230: "Advanced Data Mining",
    ST5290: "Special Topics in Statistics",
    ST6101: "Doctoral Research Seminar I",
    ST6102: "Doctoral Research Seminar II",
    ST6103: "Advanced Probability",
    ST6104: "Advanced Inference",
    ST6105: "Advanced Regression Theory",
    ST6120: "Advanced Bayesian Theory",
    ST6241: "Statistical Deep Learning",
    IND5003: "Industrial Data Analytics",
    ST5201: "Advanced Statistical Inference",
  };

  const courses = Object.keys(courseMap);

  useEffect(() => {
    if (courseCode) {
      setCourseName(courseMap[courseCode] || "Unknown Course");
    } else {
      setCourseName("");
    }
  }, [courseCode]);

  useEffect(() => {
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

  const handleExportPDF = () => {
    if (!assessmentName.trim() || !courseCode.trim()) {
      alert("Please fill in both Course Code and Assessment Name before exporting.");
      return;
    }

    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    if (localQuestions.length === 0) {
      alert("No questions to export!");
      return;
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text("National University of Singapore", 105, 15, { align: "center" });

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    doc.text(`Course Code: ${courseCode}`, 14, 30);
    doc.text(`Course Name: ${courseName}`, 14, 38);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text(`Assessment: ${assessmentName}`, 14, 48);

    let yPosition = 70;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);

    localQuestions.forEach((q, index) => {
      let questionText = `${index + 1}. ${q.question_text || "N/A"}`;
      const questionType = q.question_type?.toLowerCase() || "short";

      if (questionType === "truefalse" || questionType === "true/false") {
        questionText += "  (True / False)";
      }

      const splitText = doc.splitTextToSize(questionText, 180);
      doc.text(splitText, 14, yPosition);
      yPosition += splitText.length * 7;

      if (questionType === "mcq" && q.options?.length > 0) {
        q.options.forEach((option, i) => {
          const optionLabel = String.fromCharCode(65 + i);
          const optionText = `${optionLabel}. ${option}`;
          const splitOption = doc.splitTextToSize(optionText, 170);
          doc.text(splitOption, 20, yPosition);
          yPosition += splitOption.length * 6;
        });
      }

      yPosition += 6;
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }
    });

    const safeName = assessmentName.replace(/[^\w\s-]/g, "").replace(/\s+/g, "_");
    const filename = `${courseCode}_${safeName}_question_paper.pdf`;
    doc.save(filename);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="bg-white border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* LEFT BUTTONS */}
            <div className="flex space-x-2">
              <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Dashboard</span>
              </Button>

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

              {fromDetailsPage && onBackToDetails && selectedQuestionId && (
                <Button
                  variant="ghost"
                  onClick={() => onBackToDetails(selectedQuestionId)}
                  className="flex items-center space-x-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>Back to Question</span>
                </Button>
              )}
            </div>

          </div>

          <h1
            className="text-center mt-4 text-xl font-semibold text-gray-800"
            style={{ fontWeight: "600" }}
          >
            Question Cart
          </h1>
        </div>
      </header>

      {/* EXISTING CONTENT (unchanged) */}
      <div className="p-6 space-y-4">
        {localQuestions.length === 0 ? (
          <p className="text-gray-500 mt-4">No questions in your cart yet.</p>
        ) : (
          <div className="grid gap-4 mt-4">
            <div className="bg-gray-50 py-2">
              <h3 className="text-base font-semibold text-gray-800 mb-3">
                Assessment Details
              </h3>

              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Course Code
                </label>
                <select
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a course</option>
                  {courses.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Course Name
                </label>
                <input
                  type="text"
                  value={courseName}
                  readOnly
                  placeholder="Auto-filled from course code"
                  className="w-full px-3 py-2 border border-gray-300 bg-gray-100 rounded-lg text-gray-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Name
                </label>
                <input
                  type="text"
                  value={assessmentName}
                  onChange={(e) => setAssessmentName(e.target.value)}
                  placeholder="e.g. Quiz 2 / Midterm 24/25 S1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div style={{ marginTop: "24px" }}></div>

            <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
              {localQuestions.map((q) => (
                <Card
                  key={q.question_id}
                  className="shadow-sm hover:shadow-md transition"
                  style={{ borderRadius: "16px", overflow: "hidden" }}
                >
                  <CardContent className="p-4 space-y-2" style={{ paddingTop: "20px" }}>
                    {Array.isArray(q.concepts) && q.concepts.length > 0 && (
                      <div
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "8px",
                          fontSize: "14px",
                          color: "#000",
                          marginLeft: "4px",
                        }}
                      >
                        {q.concepts.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            style={{
                              backgroundColor: "#f0f0f0",
                              borderRadius: "16px",
                              padding: "6px 12px",
                              fontSize: "14px",
                              border: "1px solid #ddd",
                            }}
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}

                    <p
                      className="font-medium text-gray-900 line-clamp-2"
                      style={{ marginTop: "12px", marginLeft: "6px" }}
                    >
                      {q.question_text}
                    </p>

                    <p className="text-sm text-gray-500" style={{ marginLeft: "6px" }}>
                      <span>Course:</span> {q.course_code} | <span>Type:</span>{" "}
                      {q.question_type} | <span>Difficulty:</span>{" "}
                      {q.difficulty
                        ? q.difficulty.charAt(0).toUpperCase() +
                          q.difficulty.slice(1).toLowerCase()
                        : "—"}
                    </p>

                    <div className="flex space-x-2 pt-2">
                      {onBackToDetails && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onBackToDetails(q.question_id)}
                          className="flex-1"
                        >
                          <Eye style={{ marginRight: "6px" }} className="h-3 w-3" /> View Details
                        </Button>
                      )}

                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => onRemoveQuestion(q.question_id)}
                        className="flex-1"
                      >
                        <Trash2 style={{ marginRight: "6px" }} className="h-3 w-3" /> Remove
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}

              <button
                onClick={handleExportPDF}
                className="mt-2 bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700"
              >
                Export to PDF
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}