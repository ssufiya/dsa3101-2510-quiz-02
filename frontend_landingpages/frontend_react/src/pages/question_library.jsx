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
  GripVertical,
  ChevronDown,
  Plus,
  ShoppingBasket,
  Eye,
  HelpCircle,
} from "lucide-react";
import axios from "axios";

/* ------------------------- Tooltip Component ------------------------- */
function Tooltip({ text, children }) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      style={{ position: "relative", display: "inline-block" }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          style={{
            position: "absolute",
            bottom: "125%",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#111827",
            color: "white",
            padding: "6px 8px",
            borderRadius: "6px",
            fontSize: "12px",
            whiteSpace: "nowrap",
            boxShadow: "0 2px 6px rgba(0, 0, 0, 0.15)",
            zIndex: 100,
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
}

/* ------------------------- MultiSelectDropdown ------------------------- */
function MultiSelectDropdown({ label, options, selected, setSelected, searchable = false }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const toggleOption = (option) => {
    if (selected.includes(option)) {
      setSelected(selected.filter((o) => o !== option));
    } else {
      setSelected([...selected, option]);
    }
  };

  const filteredOptions = searchable
    ? options.filter((opt) => opt.toLowerCase().includes(search.toLowerCase()))
    : options;

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
            maxHeight: "260px",
            overflowY: "auto",
          }}
        >
          {searchable && (
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: "90%",
                margin: "8px",
                padding: "4px 8px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px",
              }}
            />
          )}

          {filteredOptions.length === 0 ? (
            <div style={{ padding: "8px 10px", color: "#888" }}>No matches found</div>
          ) : (
            filteredOptions.map((option) => (
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
            ))
          )}
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
                backgroundColor: selected === option ? "#f3f4f6" : "transparent",
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
      </CardHeader>

      <CardContent>
        <div className="flex space-x-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onQuestionDetails(question.question_id)}
          >
            <Eye style={{ marginRight: "6px" }} className="h-3 w-3" /> View Details
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
    matchMode: "",
  });
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const difficulties = ["Low", "Med", "High"];
  const types = ["Code", "T/F", "MCQ", "MRQ", "SRQ"];
  const courses = [
    "DSA1101", "DSA2101", "DSA3101", "ST3131", "ST3248", "ST4253", "IND5003", "ST5201",
  ];
  const matches = ["Match All", "Match Any"];

  const fetchQuestions = async (overrideFilters = {}) => {
    setLoading(true);
    try {
      const response = await axios.get("http://localhost:5003/api/questions/", {
        params: {
          difficulty: filters.difficulties.length ? filters.difficulties.join(",") : undefined,
          type: filters.types.length ? filters.types.join(",") : undefined,
          subject: filters.courses.length ? filters.courses.join(",") : undefined,
          topic: searchTerm || undefined,
          match:
            filters.matchMode === "Match Any"
              ? "any"
              : filters.matchMode === "Match All"
              ? "all"
              : undefined,
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

  useEffect(() => {
    fetchQuestions();
    const refreshHandler = () => fetchQuestions();
    window.addEventListener("refresh-questions", refreshHandler);
    return () => window.removeEventListener("refresh-questions", refreshHandler);
  }, []);

  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

  const clearFilters = () => {
    setSearchTerm("");
    setFilters({
      difficulties: [],
      types: [],
      courses: [],
      matchMode: "",
    });
    fetchQuestions({});
  };

  const removeFilterChip = (category, value) => {
    setFilters((prev) => ({
      ...prev,
      [category]: prev[category].filter((item) => item !== value),
    }));
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f9fafb", display: "flex", flexDirection: "column" }}>
      {/* HEADER */}
      <header style={{ backgroundColor: "white", borderBottom: "1px solid #e5e7eb", paddingBottom: "30px", paddingTop: "40px"}}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", height: "64px", position: "relative" }}>
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft style={{ width: "16px", height: "16px", marginRight: "4px" }} />
              Back to Dashboard
            </Button>

            <div style={{ position: "absolute", left: "50%", transform: "translateX(-50%)", textAlign: "center" }}>
              <h1 style={{ fontSize: "50px", fontWeight: "600", margin: 0 }}>Question Library</h1>
              <p style={{ fontSize: "14px", color: "#6b7280", marginTop: "8px", marginBottom: "20px" }}>
                Browse questions from the database
              </p>
            </div>

            <Button variant="ghost" onClick={onGoToQuestionCart}>
              <ShoppingBasket style={{ width: "18px", height: "18px", marginRight: "6px" }} />
              Cart ({cartQuestions.length})
            </Button>
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
        <MultiSelectDropdown label="Select Course" options={courses} selected={filters.courses} setSelected={(vals) => setFilters({ ...filters, courses: vals })} searchable={true} />
        <Input placeholder="Search for topic..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-64 rounded-lg text-center" />

        {/* Match Mode with Tooltip */}
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <SingleSelectDropdown
            label="Match Mode"
            options={matches}
            selected={filters.matchMode}
            setSelected={(val) => setFilters({ ...filters, matchMode: val })}
          />
          <Tooltip text="Match All: show only questions that meet all selected filters. Match Any: show questions matching at least one.">
            <HelpCircle
              style={{
                width: "16px",
                height: "16px",
                color: "#9ca3af",
                cursor: "pointer",
              }}
            />
          </Tooltip>
        </div>
      </div>

      {/* Filter Chips */}
      {(filters.difficulties.length > 0 ||
        filters.types.length > 0 ||
        filters.courses.length > 0) && (
        <div
          style={{
            backgroundColor: "#fff",
            borderBottom: "1px solid #e5e7eb",
            padding: "12px 24px",
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          <span style={{ fontWeight: "500", color: "#374151" }}>Active filters:</span>
          {[...filters.difficulties.map((d) => ({ category: "difficulties", label: `Difficulty: ${d}` })),
            ...filters.types.map((t) => ({ category: "types", label: `Type: ${t}` })),
            ...filters.courses.map((c) => ({ category: "courses", label: `Course: ${c}` })),
          ].map((chip, idx) => (
            <span
              key={idx}
              style={{
                backgroundColor: "#e0f2fe",
                borderRadius: "16px",
                padding: "4px 8px",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {chip.label}
              <button
                onClick={() => removeFilterChip(chip.category, chip.label.split(": ")[1])}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontWeight: "bold",
                }}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

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
        <Button onClick={() => fetchQuestions()}>Filter</Button>
        <Button variant="outline" onClick={clearFilters}>Clear</Button>
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