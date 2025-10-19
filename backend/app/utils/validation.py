"""
Validation utilities for question data
"""

def validate_question_data(question: dict) -> list:
    """
    Validate question data structure and content.
    Returns list of error messages, empty list if valid
    """
    errors = []

    required_fields = [
        'question_text', 'course_code', 'course_name', 'assessment_type', 'difficulty', 'concepts'
    ]

    for field in required_fields:
        if field not in question or not question[field]:
            errors.append(f"Missing required field; {field}")

    if 'difficulty' in question and question['difficulty']:
         valid_difficulties = ['Easy', 'Medium', 'Hard']
         if question['difficulty'] not in valid_difficulties:
            errors.append(f"difficulty must be one of : {', '.join(valid_difficulties)}")
    
    
    if 'question_type' in question and question['question_type'] == 'MCQ':
        has_options = any([
            question.get('option_a'),
            question.get('option_b'),
            question.get('option_c'),
            question.get('option_d')
        ])   
        if not has_options:
            errors.append("MCQ questions must have at least some answer options") 
        if 'correct_answer' in question and question['correct_answer']:
            valid_answers = ['A', 'B', 'C', 'D', 'E']    
            if question['correct_answer'].upper() not in valid_answers:
                        errors.append(f"For MCQ questions, correct_answer must be A, B, D, D, or E")
    elif 'question_type' in question and question['question_type'] == 'True/False':
        if 'cprrect_answer' in question and question['correct_answer']:
            valid_answers = ['True', 'false', 'TRUE', 'FALSE', 'T', 'F']    
            if question['correct_answer'].upper() not in valid_answers:
                    errors.append(f"For True/False questions, correct_answer must be True or False")
    
    return errors

def validate_filters(filters: dict) -> bool:
    valid_difficulties = ['Easy', 'Medium', 'Hard']
    if 'difficulty' in filters and filters['difficulty'] not in valid_difficulties:
          raise ValueError(f"Invalid difficulty. Must be one of : {', '.join(valid_difficulties)}")
    
    return True