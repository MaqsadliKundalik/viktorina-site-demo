from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
import os

class Command(BaseCommand):
    help = "TXT fayldan testlarni import qiladi (# savol, + to'g'ri, - noto'g'ri)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="TXT fayl yo'li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {filepath}"))
            return

        base_category_name = "KTT Testlari"
        base_quiz_title = "KTT Quiz"
        category_counter = 1

        # Boshlang'ich kategoriya va quiz
        current_category, _ = Category.objects.get_or_create(
            name=f"{base_category_name} {category_counter}"
        )
        current_quiz, _ = Quiz.objects.get_or_create(
            title=f"{base_quiz_title} {category_counter}",
            category=current_category
        )

        imported_questions = 0
        current_question = None

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('#'):
                    # Yangi savol
                    # Savollar sonini tekshirish (50 ta bo'lsa yangi quiz)
                    question_count = Question.objects.filter(quiz=current_quiz).count()
                    if question_count >= 50:
                        category_counter += 1
                        current_category, _ = Category.objects.get_or_create(
                            name=f"{base_category_name} {category_counter}"
                        )
                        current_quiz, _ = Quiz.objects.get_or_create(
                            title=f"{base_quiz_title} {category_counter}",
                            category=current_category
                        )
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ 50 savoldan oshdi, yangi kategoriya: {base_category_name} {category_counter}"
                        ))

                    question_text = line[1:].strip()
                    current_question = Question.objects.create(
                        quiz=current_quiz,
                        text=question_text
                    )
                    imported_questions += 1

                elif line.startswith('+') or line.startswith('-'):
                    if current_question:
                        is_correct = line.startswith('+')
                        answer_text = line[1:].strip()
                        Answer.objects.create(
                            question=current_question,
                            text=answer_text,
                            is_correct=is_correct
                        )

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi! {imported_questions} ta savol qo'shildi."))
