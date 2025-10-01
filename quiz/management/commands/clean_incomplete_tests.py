from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer

class Command(BaseCommand):
    help = "Ma'lumotlar bazasidan chala testlarni (savoli yoki variantlari yo'q) o'chiradi"

    def handle(self, *args, **options):
        # 1. Savoli yo'q quizlarni aniqlash va o'chirish
        quizzes_without_questions = Quiz.objects.filter(questions__isnull=True)
        quizzes_deleted = quizzes_without_questions.count()
        for quiz in quizzes_without_questions:
            self.stdout.write(self.style.WARNING(
                f"Quiz o'chirildi: {quiz.title} (ID: {quiz.id}) - sabab: savollar yo'q"
            ))
        quizzes_without_questions.delete()

        # 2. Variantlari yo'q savollarni aniqlash va o'chirish
        questions_without_answers = Question.objects.filter(answers__isnull=True)
        questions_without_answers_deleted = questions_without_answers.count()
        for question in questions_without_answers:
            self.stdout.write(self.style.WARNING(
                f"Savol o'chirildi: {question.text} (ID: {question.id}, Quiz: {question.quiz.title}) - sabab: javoblar yo'q"
            ))
        questions_without_answers.delete()

        # 3. To'g'ri javobi yo'q savollarni aniqlash va o'chirish
        questions_without_correct_answer = Question.objects.exclude(
            answers__is_correct=True
        )
        questions_without_correct_deleted = questions_without_correct_answer.count()
        for question in questions_without_correct_answer:
            self.stdout.write(self.style.WARNING(
                f"Savol o'chirildi: {question.text} (ID: {question.id}, Quiz: {question.quiz.title}) - sabab: to'g'ri javob yo'q"
            ))
        questions_without_correct_answer.delete()

        # 4. Yakuniy natijalarni chiqarish
        total_deleted = (
            quizzes_deleted +
            questions_without_answers_deleted +
            questions_without_correct_deleted
        )
        
        if total_deleted == 0:
            self.stdout.write(self.style.SUCCESS("✅ Hech qanday chala test topilmadi!"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Tozalash tugadi! O'chirildi: "
                f"{quizzes_deleted} ta quiz, "
                f"{questions_without_answers_deleted} ta javobsiz savol, "
                f"{questions_without_correct_deleted} ta to'g'ri javobsiz savol"
            ))