from django.shortcuts import render, get_object_or_404, redirect
from .models import Quiz, Question, Answer, Category

from django.shortcuts import get_object_or_404, redirect, render
import random

def quiz_list(request):
    """Barcha kategoriyalar va ularning testlarini chiqarish"""
    categories = Category.objects.prefetch_related("quizzes__questions").all()
    return render(request, "quiz_list.html", {"categories": categories})


def start_quiz(request, quiz_id):
    """Testni boshlash – session tayyorlash"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    request.session["score"] = 0
    request.session["answered"] = {}
    return redirect("quiz:quiz_question", quiz_id=quiz.id, question_index=0)

from django.shortcuts import get_object_or_404, redirect, render
import random

def quiz_question(request, quiz_id, question_index):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = list(quiz.questions.all())
    total = len(questions)

    if question_index >= total:
        return redirect("quiz:quiz_finish", quiz_id=quiz.id)

    question = questions[question_index]
    # Variantlarni har safar aralashtirish
    answers = list(question.answers.all())
    random.shuffle(answers)  # Variantlar tasodifiy tartibda aralashtiriladi
    
    answered = request.session.get("answered", {})

    feedback = None

    if request.method == "POST":
        selected_id = request.POST.get("answer")
        # To'g'ri javobning ID'sini asl ro'yxatdan olamiz
        correct_answer = question.answers.filter(is_correct=True).first()
        correct_id = correct_answer.id if correct_answer else None

        if selected_id:  # Javob tanlangan
            selected_id = int(selected_id)
            selected = Answer.objects.get(id=selected_id)
            correct = selected.is_correct

            answered[str(question.id)] = selected_id
            request.session["answered"] = answered

            if correct:
                request.session["score"] = request.session.get("score", 0) + 1

            feedback = {
                "selected_id": selected_id,
                "correct_id": correct_id,
                "is_correct": correct,
            }
        else:  # Hech narsa tanlanmagan
            feedback = {
                "selected_id": None,
                "correct_id": correct_id,
                "is_correct": False,
            }

    progress = round(((question_index + 1) / total) * 100, 2)

    return render(request, "quiz_question.html", {
        "quiz": quiz,
        "question": question,
        "answers": answers,  # Aralashtirilgan variantlar
        "index": question_index,
        "total": total,
        "feedback": feedback,
        "progress": progress,
    })


def quiz_finish(request, quiz_id):
    """Natija chiqarish"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    score = request.session.get("score", 0)
    total = quiz.questions.count()
    percent = round((score / total) * 100, 2) if total > 0 else 0

    return render(request, "quiz_finish.html", {
        "quiz": quiz,
        "score": score,
        "total": total,
        "percent": percent,
        "progress": 100,  # Natijada progress doim 100%
    })
