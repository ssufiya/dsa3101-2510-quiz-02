import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/card';
import { Button } from '../components/button';
import { Badge } from '../components/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/tabs';
import {
  ArrowLeft,
  BarChart3,
  Edit3,
  Download,
  Eye,
  HelpCircle,
  Lightbulb,
} from 'lucide-react';

export function QuestionDetails({ questionId = 'q-1', onBack = () => {}, onViewQuestion }) {
  const [questionData] = useState({
    id: 'q-1',
    question: 'What is the time complexity of inserting an element at the beginning of a linked list?',
    type: 'Multiple Choice',
    options: ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
    correctAnswer: 'O(1)',
    explanation:
      "Inserting at the beginning of a linked list only requires updating the head pointer and setting the new node's next pointer, which takes constant time.",
    courseName: 'Data Structures and Algorithms',
    courseCode: 'CS 201',
    difficulty: 'Medium',
    author: 'Dr. Sarah Chen',
    institution: 'Stanford University',
    createdAt: '2024-01-12',
    lastModified: '2024-01-15',
    tags: ['linked-list', 'time-complexity', 'algorithms'],
    subject: 'Computer Science',
    totalUsages: 245,
    uniqueInstructors: 8,
    averageScore: 72.5,
    lastUsed: '2024-01-15',
  });

  const [usageHistory] = useState([
    {
      id: 'usage-1',
      semester: 'Spring',
      year: 2024,
      course: 'CS 201',
      instructor: 'Dr. Sarah Chen',
      usageCount: 45,
      date: '2024-01-15',
      quizTitle: 'Midterm Exam - Data Structures',
    },
    {
      id: 'usage-2',
      semester: 'Fall',
      year: 2023,
      course: 'CS 201',
      instructor: 'Dr. Sarah Chen',
      usageCount: 52,
      date: '2023-10-20',
      quizTitle: 'Quiz 3 - Linked Lists and Arrays',
    },
  ]);

  const [editHistory] = useState([
    {
      id: 'edit-1',
      date: '2024-01-15',
      editor: 'Dr. Sarah Chen',
      changeType: 'Correct Answer',
      description: 'Updated correct answer explanation for clarity',
      previousValue: 'Inserting at the beginning takes constant time.',
      newValue:
        "Inserting at the beginning of a linked list only requires updating the head pointer and setting the new node's next pointer, which takes constant time.",
    },
    {
      id: 'edit-2',
      date: '2024-01-13',
      editor: 'Dr. Sarah Chen',
      changeType: 'Tags',
      description: 'Added additional tags for better categorization',
      previousValue: 'linked-list, algorithms',
      newValue: 'linked-list, time-complexity, algorithms',
    },
  ]);

  const [similarQuestions] = useState([
    {
      id: 'sq-1',
      question: 'What is the time complexity of deleting an element from the end of a linked list?',
      courseName: 'Data Structures and Algorithms',
      courseCode: 'CS 201',
      difficulty: 'Medium',
      author: 'Dr. Sarah Chen',
      institution: 'Stanford University',
      usageCount: 189,
      tags: ['linked-list', 'time-complexity', 'algorithms'],
    },
    {
      id: 'sq-2',
      question: 'Which operation on a doubly linked list has O(1) time complexity?',
      courseName: 'Advanced Data Structures',
      courseCode: 'CS 301',
      difficulty: 'Medium',
      author: 'Prof. Michael Torres',
      institution: 'MIT',
      usageCount: 156,
      tags: ['linked-list', 'doubly-linked-list', 'time-complexity'],
    },
  ]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Easy':
        return 'bg-green-100 text-green-800';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'Hard':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getChangeTypeColor = (changeType) => {
    switch (changeType) {
      case 'Created':
        return 'bg-green-100 text-green-800';
      case 'Question Text':
        return 'bg-blue-100 text-blue-800';
      case 'Correct Answer':
        return 'bg-orange-100 text-orange-800';
      case 'Tags':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 space-x-4">
            <Button variant="ghost" onClick={onBack} className="flex items-center space-x-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Library</span>
            </Button>
            <div className="h-6 w-px bg-gray-300"></div>
            <div className="flex items-center space-x-3">
              <div className="bg-primary rounded-lg p-2">
                <HelpCircle className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Question Details</h1>
                <p className="text-sm text-muted-foreground">
                  {questionData.courseCode} - {questionData.courseName}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* 🧠 Main Section */}
          <div className="flex-1 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between mb-4">
                  <Badge className={getDifficultyColor(questionData.difficulty)}>
                    {questionData.difficulty}
                  </Badge>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Edit3 className="h-4 w-4 mr-2" /> Edit
                    </Button>
                    <Button size="sm">
                      <Download className="h-4 w-4 mr-2" /> Import
                    </Button>
                  </div>
                </div>
                <CardTitle>{questionData.question}</CardTitle>
                <CardDescription>
                  By {questionData.author} • {questionData.institution}
                </CardDescription>
              </CardHeader>

              {/* ✅ Options + Correct Answer Display */}
              <CardContent>
                {questionData.options.map((option, i) => {
                  const isCorrect =
                    option.trim().toLowerCase() ===
                    questionData.correctAnswer.trim().toLowerCase();

                  return (
                    <div
                      key={i}
                      className={`p-3 border rounded-lg mb-2 flex items-center justify-between ${
                        isCorrect
                          ? 'bg-green-50 border-green-200'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <span>{String.fromCharCode(65 + i)}.</span>
                        <span>{option}</span>
                      </div>
                      {isCorrect && <span className="text-green-600 text-lg">✅</span>}
                    </div>
                  );
                })}

                {/* ✅ Show clear correct answer section */}
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-900 font-medium">
                    ✅ Correct Answer: {questionData.correctAnswer}
                  </p>
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">{questionData.explanation}</p>
                </div>
              </CardContent>
            </Card>

            {/* Tabs */}
            <Card>
              <CardHeader>
                <CardTitle>Question Analytics & History</CardTitle>
                <CardDescription>Usage and edit history</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="usage">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="usage">Usage</TabsTrigger>
                    <TabsTrigger value="changes">Changes</TabsTrigger>
                  </TabsList>
                  <TabsContent value="usage" className="space-y-3">
                    {usageHistory.map((u) => (
                      <Card key={u.id} className="p-3 border">
                        <p className="text-sm font-medium">{u.quizTitle}</p>
                        <p className="text-xs text-muted-foreground">
                          {u.course} • {u.instructor} • {u.semester} {u.year}
                        </p>
                      </Card>
                    ))}
                  </TabsContent>
                  <TabsContent value="changes" className="space-y-3">
                    {editHistory.map((e) => (
                      <Card key={e.id} className="p-3 border">
                        <Badge className={getChangeTypeColor(e.changeType)}>
                          {e.changeType}
                        </Badge>
                        <p className="text-sm">{e.description}</p>
                        <p className="text-xs text-muted-foreground">
                          {e.previousValue} → {e.newValue}
                        </p>
                      </Card>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* 🧱 Sidebar */}
          <aside className="w-full md:w-1/3 space-y-6 mt-6 md:mt-0">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Usage Statistics</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between"><span>Total Uses</span><span>{questionData.totalUsages}</span></div>
                <div className="flex justify-between"><span>Unique Instructors</span><span>{questionData.uniqueInstructors}</span></div>
                <div className="flex justify-between"><span>Average Score</span><span>{questionData.averageScore}%</span></div>
                <div className="flex justify-between"><span>Last Used</span><span>{new Date(questionData.lastUsed).toLocaleDateString()}</span></div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Question Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <span className="text-muted-foreground text-sm">Subject</span>
                  <p className="font-medium">{questionData.subject}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-sm">Course</span>
                  <p className="font-medium">{questionData.courseCode} - {questionData.courseName}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-sm">Author</span>
                  <p className="font-medium">{questionData.author}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-sm">Institution</span>
                  <p className="font-medium">{questionData.institution}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-sm">Tags</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {questionData.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Lightbulb className="h-5 w-5" />
                  <span>Similar Questions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {similarQuestions.map((sq) => (
                  <Card
                    key={sq.id}
                    className="p-3 border cursor-pointer"
                    onClick={() => onViewQuestion?.(sq.id)}
                  >
                    <p className="text-sm font-medium">{sq.question}</p>
                    <p className="text-xs text-muted-foreground">
                      {sq.courseCode} • {sq.courseName} • {sq.difficulty}
                    </p>
                  </Card>
                ))}
                <Button variant="outline" size="sm" className="w-full">
                  <Eye className="h-3 w-3 mr-2" /> View All Similar Questions
                </Button>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}
