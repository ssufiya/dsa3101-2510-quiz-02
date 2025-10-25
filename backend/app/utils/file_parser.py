"""
CSV file parser for question uploads
"""

import csv
import io 

def parse_csv(file_contents: bytes) -> list:
    """
    Parse CSV file contents and return list of question dictionaries.
    
    Required CSV columns:
    - question_text
    - course_code
    - course_name
    - assessment_type
    - difficulty
    - concepts
    
    Optional CSV columns:
    - question_type (defaults to "Open-ended", can be "MCQ", "Open-ended", or "True/False")
    - correct_answer (A/B/C/D/E for MCQ, True/False for True/False, any text for Open-ended)
    - option_a, option_b, option_c, option_d, option_e (for MCQ questions only)
    - context
    """
    try:
        # Try multiple encodings
        csv_string = None
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
        for encoding in encodings:
            try:
                csv_string = file_contents.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, use UTF-8 with error replacement
        if csv_string is None:
            csv_string = file_contents.decode('utf-8', errors='replace')
        
        csv_reader = csv.DictReader(io.StringIO(csv_string))
        questions = []
        for row in csv_reader:
            cleaned_row = {k.strip(): v.strip() if v else None for k, v in row.items()}
            question = {
                'question_text': cleaned_row.get('question_text'),
                'question_type': cleaned_row.get('question_type'),
                'course_code': cleaned_row.get('course_code'),
                'course_name': cleaned_row.get('course_name'),
                'assessment_type': cleaned_row.get('assessment_type'),
                'difficulty': cleaned_row.get('difficulty'),
                'concepts':cleaned_row.get('concepts')
            }
            if cleaned_row.get('correct_answer'):
                question['correct_answer'] = cleaned_row.get('correct_answer', '').upper()
            
            if cleaned_row.get('option_a'):
                question['option_a'] = cleaned_row.get('option_a')
            if cleaned_row.get('option_b'):
                question['option_b'] = cleaned_row.get('option_b')
            if cleaned_row.get('option_c'):
                question['option_c'] = cleaned_row.get('option_c')
            if cleaned_row.get('option_d'):
                question['option_d'] = cleaned_row.get('option_d')
            if cleaned_row.get('option_e'):
                question['option_e'] = cleaned_row.get('option_e')
            
            if cleaned_row.get('context'):
                question['context'] = cleaned_row.get('context')
            questions.append(question)
        return questions
    
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")
    
    
def parse_csv_for_version(file_contents: bytes) -> dict:
    """
    Parse CSV for a single question version update.
    Expects only one row in the csv.
    """
    questions = parse_csv(file_contents)
    if len(questions) == 0:
        raise ValueError("CSV file is empty")
    
    if len(questions) > 1:
        raise ValueError("verison update should contain only one question")
    
    return questions[0]