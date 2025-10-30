import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
} from "../components/card";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import {
  ArrowLeft,
  Paperclip,
  Notebook,
  GripVertical,
  HelpCircle,
  ChevronDown,
  Plus,
  ShoppingBasket,
} from "lucide-react";
import axios from "axios";

/* ------------------------- MultiSelectDropdown ------------------------- */
function MultiSelectDropdown({ label, options, selected, setSelected }) {
  const [open, setOpen] = useState(false);

  const toggleOption = (option) => {
    if (selected.includes(option)) {
      setSelected(selected.filter((o) => o !== option));
    } else {
      setSelected([...selected, option]);
    }
  };

  return (
    <div style={{ position: "relative", width: "190px" }}>
      <Button variant="outline" className="w-full" onClick={() => setOpen(!open)}>
        {selected.length ? selected.join(", ") : label}
        <ChevronDown style={{ marginLeft: "8px", width: "16px", height: "16px" }} />
      </Button>

      {open && (
        <div
          style={{
            position: "absolute",
            zIndex: 50,
            marginTop: "4px",
            width: "100%",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            backgroundColor: "white",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            maxHeight: "240px",
            overflowY: "auto",
          }}
        >
          {options.map((option) => (
            <label
              key={option}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "6px 8px",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={() => toggleOption(option)}
                style={{ marginRight: "6px" }}
              />
              {option}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------- SingleSelectDropdown ------------------------- */
function SingleSelectDropdown({ label, options, selected, setSelected }) {
  const [open, setOpen] = useState(false);

  const handleSelect = (option) => {
    setSelected(option);
    setOpen(false);
  };

  return (
    <div style={{ position: "relative", width: "190px" }}>
      <Button variant="outline" className="w-full" onClick={() => setOpen(!open)}>
        {selected || label}
        <ChevronDown style={{ marginLeft: "8px", width: "16px", height: "16px" }} />
      </Button>

      {open && (
        <div
          style={{
            position: "absolute",
            zIndex: 50,
            marginTop: "4px",
            width: "100%",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            backgroundColor: "white",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            maxHeight: "240px",
            overflowY: "auto",
          }}
        >
          {options.map((option) => (
            <div
              key={option}
              style={{
                padding: "8px 10px",
                cursor: "pointer",
                backgroundColor:
                  selected === option ? "#f3f4f6" : "transparent",
                fontWeight: selected === option ? "500" : "400",
              }}
              onClick={() => handleSelect(option)}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------------------------- Question Card ---------------------------- */
function QuestionCard({ question, onQuestionDetails, onAddToCart, isInCart }) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        {/* Metadata */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <Paperclip className="h-4 w-4" />
            <span>{question.question_id || 0}</span>
          </div>
          <div className="flex items-center space-x-2">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
            <Badge>{question.question_type}</Badge>
          </div>
        </div>

        {/* Question text */}
        <div
          style={{
            textAlign: "center",
            fontWeight: "bold",
            fontSize: "18px",
            color: "#000",
            marginBottom: "28px",
          }}
        >
          {question.question_text || "No question text available"}
        </div>

        {/* Course + difficulty */}
        <div className="text-center text-sm text-muted-foreground mb-3">
          <div>Course Code: {question.course_code || "—"}</div>
          <div>
            Difficulty:{" "}
            {question.difficulty
              ? question.difficulty.charAt(0).toUpperCase() +
                question.difficulty.slice(1).toLowerCase()
              : "—"}
          </div>
        </div>

        {/* Concepts */}
        {Array.isArray(question.concepts) && question.concepts.length > 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flexWrap: "wrap",
              marginBottom: "16px",
              fontSize: "16px",
              color: "#000",
            }}
          >
            <span style={{ fontWeight: "500", marginRight: "8px" }}>Concepts:</span>
            {question.concepts.slice(0, 3).map((tag, idx) => (
              <span
                key={idx}
                style={{
                  backgroundColor: "#f0f0f0",
                  borderRadius: "16px",
                  padding: "6px 12px",
                  marginRight: "8px",
                  fontSize: "14px",
                  border: "1px solid #ddd",
                }}
              >
                {tag.trim()}
              </span>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent>
        <div className="flex space-x-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onQuestionDetails(question.question_id)}
          >
            View Details
          </Button>
          <Button
            size="sm"
            className="flex-1"
            onClick={() => onAddToCart(question)}
            disabled={isInCart(question.question_id)}
          >
            <Plus className="h-4 w-4 mr-1" />
            {isInCart(question.question_id) ? "Added to Cart" : "Add to Cart"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------- Main Component ------------------------- */
export function QuestionLibrary({
  onBack,
  onQuestionDetails,
  onAddToCart,
  cartQuestions = [],
  onGoToQuestionCart,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    difficulties: [],
    types: [],
    courses: [],
    semesters: [],
    matchMode: "",
  });
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const difficulties = ["Low", "Med", "High"];
  const types = ["Code", "T/F", "MCQ", "MRQ", "SRQ"];
  const courses = ["DSA1101", "IND5003", "ST1131", "ST2131", "ST2137"];
  const semesters = ["AY23/24 Sem 1", "AY23/24 Sem 2"];
  const matches = ["Match All", "Match Any"];

  /* --- Fetch Questions (correct logic from first version) --- */
  const fetchQuestions = async (overrideFilters = {}) => {
    setLoading(true);
    try {
      const response = await axios.get("http://localhost:5003/api/questions/", {
        params: {
          difficulty: filters.difficulties.length ? filters.difficulties.join(",") : undefined,
          type: filters.types.length ? filters.types.join(",") : undefined,
          subject: filters.courses.length ? filters.courses.join(",") : undefined,
          semester: filters.semesters.length ? filters.semesters.join(",") : undefined,
          topic: searchTerm || undefined,
          match: filters.matchMode || undefined,
          fuzzy: true,
          ...overrideFilters,
        },
      });
      setQuestions(response.data.data || response.data || []);
    } catch (err) {
      console.error("Error fetching questions:", err);
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  };

  /* --- Auto-fetch on mount + event listener --- */
  useEffect(() => {
    fetchQuestions();
    const refreshHandler = () => fetchQuestions();
    window.addEventListener("refresh-questions", refreshHandler);
    return () => window.removeEventListener("refresh-questions", refreshHandler);
  }, []);

  /* --- Helpers --- */
  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

  const clearFilters = () => {
    setSearchTerm("");
    setFilters({
      difficulties: [],
      types: [],
      courses: [],
      semesters: [],
      matchMode: "",
    });
    fetchQuestions({});
  };

  /* --- Render --- */
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f9fafb", display: "flex", flexDirection: "column" }}>
      {/* HEADER */}
      <header style={{ backgroundColor: "white", borderBottom: "1px solid #e5e7eb", paddingBottom: "30px", }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", height: "64px", position: "relative" }}>
            {/* Left: Back */}
            <div>
              <Button variant="ghost" onClick={onBack}>
                <ArrowLeft style={{ width: "16px", height: "16px", marginRight: "4px" }} />
                Back to Dashboard
              </Button>
            </div>

            {/* Center: Title */}
            <div style={{ position: "absolute", left: "50%", transform: "translateX(-50%)", textAlign: "center" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", marginTop: "30px"}}>
                <div>
                  <h1 style={{ fontSize: "50px", fontWeight: "600", margin: 0 }}>Question Library</h1>
                  <p style={{ fontSize: "14px", color: "#6b7280",  marginTop: "8px", marginBottom: "20px"}}>Browse questions from the database</p>
                </div>
              </div>
            </div>

            {/* Right: Cart */}
            <div>
              <Button variant="ghost" onClick={onGoToQuestionCart}>
                <ShoppingBasket style={{ width: "18px", height: "18px", marginRight: "6px" }} />
                Cart ({cartQuestions.length})
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* FILTER BAR */}
      <div
        style={{
          backgroundColor: "#f3f4f6",
          padding: "16px 24px",
          display: "flex",
          flexWrap: "wrap",
          gap: "16px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <MultiSelectDropdown label="Select Difficulty" options={difficulties} selected={filters.difficulties} setSelected={(vals) => setFilters({ ...filters, difficulties: vals })} />
        <MultiSelectDropdown label="Select Type" options={types} selected={filters.types} setSelected={(vals) => setFilters({ ...filters, types: vals })} />
        <MultiSelectDropdown label="Select Course" options={courses} selected={filters.courses} setSelected={(vals) => setFilters({ ...filters, courses: vals })} />
        <MultiSelectDropdown label="Select Semester" options={semesters} selected={filters.semesters} setSelected={(vals) => setFilters({ ...filters, semesters: vals })} />
        <Input placeholder="Search for topic..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-64 rounded-lg text-center" />
        <SingleSelectDropdown label="Filter by" options={["Match All", "Match Any"]} selected={filters.matchMode} setSelected={(val) => setFilters({ ...filters, matchMode: val })} />
      </div>

      {/* ACTION BUTTONS */}
      <div
        style={{
          backgroundColor: "white",
          borderBottom: "1px solid #e5e7eb",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "flex-end",
          gap: "12px",
        }}
      >
        <Button onClick={() => fetchQuestions()}>
          Filter
        </Button> 
        <Button variant="outline" onClick={clearFilters}>
          Clear
        </Button>
      </div>

      {/* QUESTION GRID */}
      <div className="p-6" style={{ backgroundColor: "white" }}>
        {loading ? (
          <p>Loading questions...</p>
        ) : questions.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <p>No questions found.</p>
          </div>
        ) : (
          <>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">
                Showing {questions.length} question{questions.length !== 1 ? "s" : ""}...
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {questions.map((q) => (
                <QuestionCard
                  key={q.question_id}
                  question={q}
                  onQuestionDetails={onQuestionDetails}
                  onAddToCart={onAddToCart}
                  isInCart={isInCart}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}