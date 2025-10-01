from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from docx import Document
import re

class Command(BaseCommand):
    help = "DOCX fayldan testlarni import qiladi (jadval ko‘rinishidagi savollarni)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="DOCX fayl yo'li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        doc = Document(filepath)

        base_category_name = "BOI 2025 Testlari"
        base_quiz_title = "Identifikatsiya va Modellashtirish"
        category_counter = 1

        # Kategoriya yaratish
        current_category, _ = Category.objects.get_or_create(
            name=f"{base_category_name} {category_counter}"
        )
        current_quiz, _ = Quiz.objects.get_or_create(
            title=f"{base_quiz_title} {category_counter}",
            category=current_category
        )

        imported = 0

        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]

                # Jadvalning birinchi qatori (header) bo‘lsa tashlab ketamiz
                if not cells or cells[0] == "Савол":
                    continue

                question_text = cells[0]
                answers = []

                # To‘g‘ri javob — 2-ustun
                if len(cells) > 1:
                    answers.append((cells[1], True))

                # Qolganlari noto‘g‘ri javoblar
                for cell in cells[2:]:
                    answers.append((cell, False))

                # Limit tekshiruvi
                question_count = Question.objects.filter(quiz__category=current_category).count()
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

                # Savolni DB ga yozish
                current_question = Question.objects.create(
                    quiz=current_quiz,
                    text=question_text
                )
                for ans_text, is_correct in answers:
                    Answer.objects.create(
                        question=current_question,
                        text=ans_text,
                        is_correct=is_correct
                    )

                imported += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi! {imported} ta savol qo'shildi."))


