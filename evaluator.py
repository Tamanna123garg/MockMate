def evaluate_answer(answer):
    """
    Enhanced evaluation:
    - Keyword-based scoring
    - Personalized suggestions for improvement
    """
    keywords = {
        "array": "Include how arrays store data and time complexity.",
        "stack": "Mention LIFO property and operations (push/pop).",
        "queue": "Explain FIFO and differences from stack.",
        "recursion": "Try to explain base case and recursive calls.",
        "time": "Include Big-O notation for efficiency.",
        "complexity": "Mention best/worst case scenarios.",
        "data": "Give examples of data structures.",
        "structure": "Explain its role in organizing data.",
        "process": "Include OS process handling.",
        "thread": "Explain multithreading advantages.",
        "memory": "Mention memory allocation/management.",
        "management": "Relate to resources/process management."
    }

    score = 0
    suggestions = []

    for word, suggestion in keywords.items():
        if word in answer.lower():
            score += 2
        else:
            suggestions.append(suggestion)

    if score > 10:
        score = 10

    feedback = "Good answer. Keep practicing!" if score >= 6 else "Needs improvement. Revise fundamentals."

    return score, feedback, suggestions

