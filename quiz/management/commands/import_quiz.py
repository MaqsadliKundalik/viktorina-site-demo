from django.core.management.base import BaseCommand
from docx import Document
from quiz.models import Quiz, Question, Answer, Category
import re

class Command(BaseCommand):
    help = "DOCX fayldan testlarni import qiladi (Category + Quiz bilan)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="DOCX fayl yo‘li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        doc = Document(filepath)

        current_category = None
        current_quiz = None
        current_question = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Bo‘lim (Category + Quiz) aniqlash
            if re.match(r"^[IVXLC]+\.", text):  # Rim raqami bilan boshlangan
                # Masalan: "I. Gidromeliorativ tizimlarni avtomatlashtirishning asosiy tushunchalari (1-10)"
                parts = text.split(" ", 1)
                cat_name = parts[0]  # "I."
                quiz_title = parts[1] if len(parts) > 1 else "No title"

                current_category, _ = Category.objects.get_or_create(name=cat_name)
                current_quiz, _ = Quiz.objects.get_or_create(
                    title=quiz_title,
                    category=current_category
                )
                continue

            # Savol aniqlash
            if text.startswith("Savol:"):
                if not current_quiz:
                    self.stdout.write(self.style.WARNING("⚠️ Quiz aniqlanmadi, Default quiz yaratiladi."))
                    current_category, _ = Category.objects.get_or_create(name="Default")
                    current_quiz, _ = Quiz.objects.get_or_create(title="Default", category=current_category)

                current_question = Question.objects.create(
                    quiz=current_quiz,
                    text=text.replace("Savol:", "").strip()
                )
                continue

            # Javob variantlari
            if current_question and re.match(r"^[abcd]\)", text.lower()):
                is_correct = any(run.bold for run in para.runs if run.text.strip())
                Answer.objects.create(
                    question=current_question,
                    text=text[2:].strip(),
                    is_correct=is_correct
                )

        self.stdout.write(self.style.SUCCESS("✅ Import muvaffaqiyatli tugadi!"))
