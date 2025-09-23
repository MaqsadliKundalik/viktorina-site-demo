from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from docx import Document
import re

class Command(BaseCommand):
    help = "DOCX fayldan testlarni import qiladi (har bir kategoriyada 50 savoldan ko‘p bo‘lmasligi uchun yangi kategoriya yaratiladi)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="DOCX fayl yo‘li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        doc = Document(filepath)

        current_category = None
        current_quiz = None
        current_question = None
        current_answers = []
        category_counter = 1  # Kategoriya nomlari uchun raqam

        # Default category and quiz
        base_category_name = "Gidromeliorativ Tizimlar"
        base_quiz_title = "Avtomatlashtirish Testlari"

        # Mavjud kategoriyalarni tekshirish uchun
        existing_categories = Category.objects.filter(name__startswith=base_category_name).order_by('name')
        if existing_categories.exists():
            last_category_name = existing_categories.last().name
            match = re.search(r'\d+$', last_category_name)
            if match:
                category_counter = int(match.group()) + 1
            else:
                category_counter = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Category and Quiz detection (e.g., "I. Some Title")
            if re.match(r"^[IVXLC]+\.", text):
                parts = text.split(" ", 1)
                cat_name = parts[0]  # e.g., "I."
                quiz_title = parts[1] if len(parts) > 1 else f"{base_quiz_title} {category_counter}"

                # Kategoriyani yaratish yoki olish
                current_category, _ = Category.objects.get_or_create(name=cat_name)
                # Kategoriyadagi savollar sonini tekshirish
                question_count = Question.objects.filter(quiz__category=current_category).count()
                if question_count >= 50:
                    self.stdout.write(self.style.WARNING(f"⚠️ Kategoriya '{cat_name}'da 50 yoki undan ko‘p savol bor, yangi default kategoriya yaratiladi."))
                    category_counter += 1
                    current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
                    quiz_title = f"{base_quiz_title} {category_counter}"

                current_quiz, _ = Quiz.objects.get_or_create(
                    title=quiz_title,
                    category=current_category
                )
                continue
            else:
                # Agar kategoriya topilmasa, default yaratamiz yoki ishlatamiz
                if not current_category:
                    self.stdout.write(self.style.WARNING("⚠️ Kategoriya aniqlanmadi, Default category yaratiladi yoki ishlatiladi."))
                    current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
                    question_count = Question.objects.filter(quiz__category=current_category).count()
                    if question_count >= 50:
                        self.stdout.write(self.style.WARNING(f"⚠️ Kategoriya '{current_category.name}'da 50 yoki undan ko‘p savol bor, yangi kategoriya yaratiladi."))
                        category_counter += 1
                        current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")

                if not current_quiz:
                    self.stdout.write(self.style.WARNING("⚠️ Quiz aniqlanmadi, Default quiz yaratiladi."))
                    current_quiz, _ = Quiz.objects.get_or_create(
                        title=f"{base_quiz_title} {category_counter}",
                        category=current_category
                    )

            # Question detection (starts with #)
            if text.startswith("#"):
                # Oldingi savolni saqlash
                if current_question and current_answers:
                    for ans_text, is_correct in current_answers:
                        Answer.objects.create(
                            question=current_question,
                            text=ans_text,
                            is_correct=is_correct
                        )
                    current_answers = []

                # Yangi savol yaratish
                question_text = text[1:].strip()  # Remove #
                current_question = Question.objects.create(
                    quiz=current_quiz,
                    text=question_text
                )
                continue

            # Variant detection (old format: + or -)
            if current_question and text.startswith(("+", "-")):
                is_correct = text.startswith("+")
                ans_text = text[1:].strip()
                current_answers.append((ans_text, is_correct))

            # Variant detection (new format: ==== or ++++)
            elif current_question and (text.startswith("====") or text.startswith("++++")):
                is_correct = text.startswith("++++")
                ans_text = text[4:].strip()  # Remove ==== or ++++
                current_answers.append((ans_text, is_correct))

        # Oxirgi savolning javoblarini saqlash
        if current_question and current_answers:
            for ans_text, is_correct in current_answers:
                Answer.objects.create(
                    question=current_question,
                    text=ans_text,
                    is_correct=is_correct
                )

        self.stdout.write(self.style.SUCCESS("✅ Import muvaffaqiyatli tugadi!"))
