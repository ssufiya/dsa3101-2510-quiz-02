import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/card";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { Badge } from "../components/badge";
import { ArrowLeft, Bookmark, GripVertical, HelpCircle, ChevronDown, Plus, ShoppingBasket } from "lucide-react";
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
      <Button
        variant="outline"
        className="w-full justify-between"
        onClick={() => setOpen(!open)}
      >
        {selected.length ? selected.join(", ") : label}
        <ChevronDown className="ml-2 h-4 w-4" />
      </Button>
      {open && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto">
          {options.map((option) => (
            <label key={option} className="flex items-center px-2 py-1 cursor-pointer hover:bg-gray-100">
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
      <Button
        variant="outline"
        className="w-full justify-between"
        onClick={() => setOpen(!open)}
      >
        {selected || label}
        <ChevronDown className="ml-2 h-4 w-4" />
      </Button>

      {open && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto">
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
  const getTypeColor = (type) => {
    switch (type) {
      case "MCQ":
      case "Multiple Choice": return "bg-blue-100 text-blue-800";
      case "T/F":
      case "True/False": return "bg-purple-100 text-purple-800";
      case "Short Answer": return "bg-orange-100 text-orange-800";
      case "Essay": return "bg-pink-100 text-pink-800";
      case "Code": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <Bookmark className="h-4 w-4" />
            <span>{question.question_id || 0}</span>
          </div>
          <div className="flex items-center space-x-2">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
            <Badge className={getTypeColor(question.question_type)}>{question.question_type}</Badge>
          </div>
        </div>
        <CardTitle className="text-lg leading-relaxed">{question.assessment_type || "—"}</CardTitle>
        <CardDescription>
          <span className="block font-medium text-foreground">{question.course_code}</span>
          <span className="block text-sm text-muted-foreground">Difficulty: {question.difficulty}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground line-clamp-3">{question.question_text}</div>
          {Array.isArray(question.concepts) && question.concepts.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {question.concepts.slice(0, 3).map((tag, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">{tag.trim()}</Badge>
              ))}
            </div>
          )}
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
              {isInCart(question.question_id) ? "Added to Preview" : "Add to Preview"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// --- QuestionLibrary ---
export function QuestionLibrary({ onBack, onQuestionDetails, onAddToCart, cartQuestions = [], onGoToQuestionCart }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDifficulties, setSelectedDifficulties] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [selectedSemesters, setSelectedSemesters] = useState([]);
  const [matchMode, setMatchMode] = useState("");
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const difficulties = ["low", "med", "hard"];
  const types = ["Code", "T/F", "MCQ", "MRQ", "SRQ"];
  const courses = ["DSA1101", "IND5003", "ST1131", "ST2131", "ST2137"];
  const semesters = ["AY23/24 Sem 1", "AY23/24 Sem 2"];
  const matches = ["Match All", "Match Any"];

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const response = await axios.get("http://localhost:5003/api/questions/", {
        params: {
          difficulty: selectedDifficulties.length ? selectedDifficulties.join(",") : undefined,
          type: selectedTypes.length ? selectedTypes.join(",") : undefined,
          subject: selectedCourses.length ? selectedCourses.join(",") : undefined,
          semester: selectedSemesters.length ? selectedSemesters.join(",") : undefined,
          topic: searchTerm || undefined,
          match: matchMode || undefined,
          fuzzy: true,
          is_latest: true,
        },
      });
      setQuestions(response.data.data || []);
    } catch (error) {
      console.error("Error fetching questions:", error);
    } finally {
      setLoading(false);
    }
  };

  // <<< NEW: fetch all questions on page load
  useEffect(() => {
    fetchQuestions();
  }, []);

  const isInCart = (id) => cartQuestions.some((q) => q.question_id === id);

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
          <Input
            placeholder="Search by keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />

          <MultiSelectDropdown label="Select Difficulty" options={difficulties} selected={selectedDifficulties} setSelected={setSelectedDifficulties} />
          <MultiSelectDropdown label="Select Type" options={types} selected={selectedTypes} setSelected={setSelectedTypes} />
          <MultiSelectDropdown label="Select Course" options={courses} selected={selectedCourses} setSelected={setSelectedCourses} />
          <MultiSelectDropdown label="Select Semester" options={semesters} selected={selectedSemesters} setSelected={setSelectedSemesters} />
          <SingleSelectDropdown label="Select Match Mode" options={matches} selected={matchMode} setSelected={setMatchMode} />

          <Button onClick={fetchQuestions} className="ml-2">Filter</Button>
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
          {loading ? <p>Loading questions...</p> :
            questions.length === 0 ? (
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