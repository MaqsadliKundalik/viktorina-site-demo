from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from docx import Document
import re

class Command(BaseCommand):
    help = "DOCX fayldan matn ko‘rinishidagi testlarni import qiladi (savollar # bilan, javoblar + va - bilan)"

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
        current_question_text = None
        answers = []

        # Matnni paragraf bo'yicha o'qish
        for para in doc.paragraphs:
            text = para.text.strip()

            # Bo'sh paragrafni o'tkazib yuborish
            if not text:
                continue

            # Savol boshlanishi (# bilan)
            if text.startswith('#'):
                # Agar oldin savol bo'lsa, uni saqlaymiz
                if current_question_text and answers:
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
                        text=current_question_text
                    )
                    for ans_text, is_correct in answers:
                        Answer.objects.create(
                            question=current_question,
                            text=ans_text,
                            is_correct=is_correct
                        )
                    imported += 1

                # Yangi savolni boshlash
                current_question_text = text[1:].strip()  # # belgisini olib tashlaymiz
                answers = []

            # To'g'ri javob (+ bilan)
            elif text.startswith('+'):
                answers.append((text[1:].strip(), True))

            # Noto'g'ri javob (- bilan)
            elif text.startswith('-'):
                answers.append((text[1:].strip(), False))

        # Oxirgi savolni saqlash
        if current_question_text and answers:
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
                text=current_question_text
            )
            for ans_text, is_correct in answers:
                Answer.objects.create(
                    question=current_question,
                    text=ans_text,
                    is_correct=is_correct
                )
            imported += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi! {imported} ta savol qo'shildi."))
