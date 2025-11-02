import { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/card';
import { Button } from '../components/button';
import { Badge } from '../components/badge';
import { Progress } from '../components/progress';
import { Alert, AlertDescription } from '../components/alert';
import { 
  Plus, BookOpen, Edit, Trash2, Eye, LogOut, Users, 
  BarChart3, BookOpenText, Upload, FileText, CheckCircle, 
  AlertCircle, Download, ShoppingBasket
} from 'lucide-react';

export function Homepage({
  onLogout,
  onCreateQuiz,
  onEditQuiz,
  onViewQuiz,
  onGoToQuestionLibrary,
  onGoToUpload,
  onGoToQuestionCart,
  cartQuestions = [], 
}) {
  const [quizzes] = useState([]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="w-full px-0">
          <div className="flex justify-between items-center h-16 px-6">
            <div className="flex items-center space-x-3">
              <div className="bg-primary rounded-lg p-2"></div>
              <div>
                <h1 className="text-xl">Quiz Bank</h1>
                <p className="text-sm text-muted-foreground">
                  A portal for managing questions and assessments for Department of Statistics & Data Science
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={onGoToQuestionLibrary}>
                <span className="flex items-center">
                  <BookOpenText className="h-4 w-4" />
                  <span style={{ display: "inline-block", width: "6px" }}></span>
                  <span>Question Library</span>
                </span>
              </Button>

              <Button
                variant="ghost"
                onClick={onLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span style={{ display: "inline-block", width: "6px" }}></span>
                <span>Logout</span>
              </Button>

              <Button
                variant="ghost"
                onClick={onGoToQuestionCart}
                className="flex items-center space-x-2"
              >
                <ShoppingBasket className="h-4 w-4" />
                <span style={{ display: "inline-block", width: "6px" }}></span>
                <span>Cart ({cartQuestions.length})</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl">Upload Quizzes</h2>
            <p className="text-muted-foreground">
              Add your latest quiz to the repository!
            </p>
          </div>
          <Button onClick={onGoToUpload} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Upload Here!</span>
          </Button>
        </div>

      </div>
    </div>
  );
}