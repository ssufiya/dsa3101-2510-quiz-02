import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { ArrowLeft, StickyNote, GripVertical, HelpCircle, ChevronDown, Plus, ShoppingBasket, Tag } from "lucide-react";
import axios from "axios";

// --- MultiSelectDropdown ---
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
    <div className="relative w-48">
      <Button variant="outline" className="w-full justify-between" onClick={() => setOpen(!open)}>
        {selected.length ? selected.join(", ") : label}
        <ChevronDown className="ml-2 h-4 w-4" />
      </Button>
      {open && (
        <div
          className="absolute z-50 mt-1 w-full border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto"
          style={{
            backgroundColor: "white",
            opacity: 1,
            backdropFilter: "none",
            WebkitBackdropFilter: "none",
          }}
        >
          {options.map((option) => (
            <label
              key={option}
              className="flex items-center px-2 py-1 cursor-pointer hover:bg-gray-100"
            >
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={() => toggleOption(option)}
                className="mr-2"
              />
              {option}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

// --- SingleSelectDropdown ---
function SingleSelectDropdown({ label, options, selected, setSelected }) {
  const [open, setOpen] = useState(false);

  const handleSelect = (option) => {
    setSelected(option);
    setOpen(false);
  };

  return (
    <div className="relative w-48">
      <Button variant="outline" className="w-full justify-between" onClick={() => setOpen(!open)}>
        {selected || label}
        <ChevronDown className="ml-2 h-4 w-4" />
      </Button>
      {open && (
        <div
          className="absolute z-50 mt-1 w-full border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto"
          style={{
            backgroundColor: "white",
            opacity: 1,
            backdropFilter: "none",
            WebkitBackdropFilter: "none",
          }}
        >
          {options.map((option) => (
            <div
              key={option}
              className={`px-3 py-2 cursor-pointer hover:bg-gray-100 ${
                selected === option ? "bg-gray-100 font-medium" : ""
              }`}
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

// --- QuestionCard ---
function QuestionCard({ question, onQuestionDetails, onAddToCart, isInCart }) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>

        {/* --- Metadata row (ID + type) --- */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <StickyNote className="h-4 w-4" />
            <span>{question.question_id || 0}</span>
          </div>
          <div className="flex items-center space-x-2">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
            <Badge>{question.question_type}
            </Badge>
          </div>
        </div>

        {/* --- Question Text (bold + centered) --- */}
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

        {/* --- Course code + difficulty --- */}
        <div className="text-center text-sm text-muted-foreground mb-3">
          <div>Course Code: {question.course_code || "—"}</div>
          <div>
            Difficulty:{" "}
            {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1).toLowerCase()}
          </div>
        </div>


        {/* --- Concept tags --- */}
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
        {/* --- Buttons --- */}
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

// --- QuestionLibrary ---
export function QuestionLibrary({ onBack, onQuestionDetails, onAddToCart, cartQuestions = [], onGoToQuestionCart }) {
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
          is_latest: undefined,
          ...overrideFilters,
        },
      });
      setQuestions(response.data.data || []);
    } catch {
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
      semesters: [],
      matchMode: "",
    });
    fetchQuestions({
      difficulty: undefined,
      type: undefined,
      subject: undefined,
      semester: undefined,
      topic: undefined,
      match: undefined,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center h-16 justify-between">
              <div className="flex items-center space-x-4">
                <Button variant="ghost" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4" />
                  <span>Back to Dashboard</span>
                </Button>
                <div className="h-6 w-px bg-gray-300"></div>
                <div className="flex items-center space-x-3">
                  <div className="bg-primary rounded-lg p-2">
                    <HelpCircle className="h-6 w-6 text-primary-foreground" />
                  </div>
                  <div>
                    <h1 className="text-xl font-semibold">Question Library</h1>
                    <p className="text-sm text-muted-foreground">Browse questions from the database</p>
                  </div>
                </div>
              </div>

              <Button variant="ghost" onClick={onGoToQuestionCart} className="flex items-center space-x-2">
                <ShoppingBasket className="h-5 w-5" />
                <span>Cart ({cartQuestions.length})</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Filters */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap gap-4 items-end">
          <MultiSelectDropdown
            label="Select Difficulty"
            options={difficulties}
            selected={filters.difficulties}
            setSelected={(vals) => setFilters({ ...filters, difficulties: vals })}
          />
          <MultiSelectDropdown
            label="Select Type"
            options={types}
            selected={filters.types}
            setSelected={(vals) => setFilters({ ...filters, types: vals })}
          />
          <MultiSelectDropdown
            label="Select Course"
            options={courses}
            selected={filters.courses}
            setSelected={(vals) => setFilters({ ...filters, courses: vals })}
          />
          <MultiSelectDropdown
            label="Select Semester"
            options={semesters}
            selected={filters.semesters}
            setSelected={(vals) => setFilters({ ...filters, semesters: vals })}
          />
          <Input
            placeholder="Search for topic..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />
          <SingleSelectDropdown
            label="Select Match Mode"
            options={matches}
            selected={filters.matchMode}
            setSelected={(val) => setFilters({ ...filters, matchMode: val })}
          />
        </div>

        {/* Buttons */}
        <div className="bg-white border-b border-gray-200 px-6 py-2 flex justify-end gap-2">
          <Button 
            onClick={() => fetchQuestions()}
            style = {{backgroundColor: "#ec4899"}}
            >Filter</Button>
          <Button variant="outline" onClick={clearFilters}>Clear</Button>
        </div>

        {/* Question List */}
        <div className="p-6">
          {!loading && questions.length > 0 && (
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">
                Showing {questions.length} question{questions.length !== 1 ? "s" : ""}...
              </h2>
            </div>
          )}
          {loading ? (
            <p>Loading questions...</p>
          ) : questions.length === 0 ? (
            <div className="text-center text-gray-500 mt-10">
              <p>No questions found.</p>
            </div>
          ) : (
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
          )}
        </div>
      </div>
    </div>
  );
}