import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/card";
import { Button } from "../components/button";
import { ArrowLeft } from "lucide-react";

export function QuestionCart({ onBack, cartQuestionIds }) {
  const [questions, setQuestions] = useState([]);

  useEffect(() => {
    // simulate API fetch using fake data
    const fakeApiResponse = [
      { id: 1, question: "What is the capital of France?", answer: "Paris" },
      { id: 2, question: "Solve 5 + 7", answer: "12" },
      { id: 3, question: "Who wrote Hamlet?", answer: "Shakespeare" },
    ];})

    // filter to match the selected IDs
    {/*const selected = fakeApiResponse.filter(q => cartQuestionIds.includes(q.id));
    setQuestions(selected);
  }, [cartQuestionIds]);*/}

  return (
    <div className="p-6 space-y-4">
      <Button variant="ghost" onClick={onBack}>
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Dashboard</span>
      </Button>
      <h2 className="text-xl font-bold">Preview Selected Questions</h2>

      {/*{questions.length === 0 ? (
        <p className="text-gray-500">No questions in your cart yet.</p>
      ) : (
        <div className="grid gap-4">
          {questions.map(q => (
            <Card key={q.id} className="shadow-sm">
              <CardHeader>
                <CardTitle>Question #{q.id}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium mb-2">{q.question}</p>
                <p className="text-sm text-muted-foreground">Answer: {q.answer}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}*/}
    </div>
  );
}
