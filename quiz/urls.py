from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("<int:quiz_id>/start/", views.start_quiz, name="start_quiz"),
    path("<int:quiz_id>/question/<int:question_index>/", views.quiz_question, name="quiz_question"),
    path("<int:quiz_id>/finish/", views.quiz_finish, name="quiz_finish"),
]
