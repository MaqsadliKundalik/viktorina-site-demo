from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from docx import Document
import re

class Command(BaseCommand):
    help = "DOCX fayldan testlarni import qiladi (har bir kategoriyada 50 savoldan ko'p bo'lmasligi uchun yangi kategoriya yaratiladi)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="DOCX fayl yo'li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        doc = Document(filepath)

        current_category = None
        current_quiz = None
        current_question = None
        current_answers = []
        category_counter = 1

        base_category_name = "BOI 2025 Testlari"  # Yangi fayl uchun moslashtirildi
        base_quiz_title = "Identifikatsiya va Modellashtirish"

        # Mavjud kategoriyalarni tekshirish
        existing_categories = Category.objects.filter(name__startswith=base_category_name).order_by('name')
        if existing_categories.exists():
            last_category_name = existing_categories.last().name
            match = re.search(r'\d+$', last_category_name)
            if match:
                category_counter = int(match.group()) + 1

        # Default kategoriya va quiz yaratish
        if not current_category:
            current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
            question_count = Question.objects.filter(quiz__category=current_category).count()
            if question_count >= 50:
                category_counter += 1
                current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
            current_quiz, _ = Quiz.objects.get_or_create(
                title=f"{base_quiz_title} {category_counter}",
                category=current_category
            )

        state = 'start'  # State machine: start, question, separator1, correct_answer, separator2, answer2, etc.

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            if text == "++++":
                # Oldingi savolni saqlash
                if current_question and current_answers:
                    for ans_text, is_correct in current_answers:
                        Answer.objects.create(
                            question=current_question,
                            text=ans_text,
                            is_correct=is_correct
                        )
                    # Kategoriya limit tekshiruvi (keyingi savol uchun)
                    question_count = Question.objects.filter(quiz__category=current_category).count()
                    if question_count >= 50:
                        category_counter += 1
                        current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
                        current_quiz, _ = Quiz.objects.get_or_create(
                            title=f"{base_quiz_title} {category_counter}",
                            category=current_category
                        )
                        self.stdout.write(self.style.WARNING(f"⚠️ 50 savoldan oshdi, yangi kategoriya: {base_category_name} {category_counter}"))

                current_question = None
                current_answers = []
                state = 'question'
                continue

            if state == 'question':
                # Savol matni
                question_text = text
                # Limit tekshiruvi
                question_count = Question.objects.filter(quiz__category=current_category).count()
                if question_count >= 50:
                    category_counter += 1
                    current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
                    current_quiz, _ = Quiz.objects.get_or_create(
                        title=f"{base_quiz_title} {category_counter}",
                        category=current_category
                    )
                    self.stdout.write(self.style.WARNING(f"⚠️ Kategoriya to'ldi, yangi kategoriya yaratildi."))
                current_question = Question.objects.create(
                    quiz=current_quiz,
                    text=question_text
                )
                state = 'separator1'
                continue

            elif state == 'separator1' and text == "====":
                state = 'correct_answer'
                continue

            elif state == 'correct_answer':
                # To'g'ri javob (# bilan)
                if text.startswith('#'):
                    ans_text = text[1:].strip()
                    current_answers.append((ans_text, True))
                else:
                    # Xato bo'lsa, noto'g'ri deb hisobla
                    current_answers.append((text, False))
                state = 'separator2'
                continue

            elif state == 'separator2' and text == "====":
                state = 'answer2'
                continue

            elif state == 'answer2':
                # Ikkinchi javob (noto'g'ri)
                current_answers.append((text, False))
                state = 'separator3'
                continue

            elif state == 'separator3' and text == "====":
                state = 'answer3'
                continue

            elif state == 'answer3':
                # Uchinchi javob
                current_answers.append((text, False))
                state = 'separator4'
                continue

            elif state == 'separator4' and text == "====":
                state = 'answer4'
                continue

            elif state == 'answer4':
                # To'rtinchi javob
                current_answers.append((text, False))
                state = 'end_block'
                continue

        # Oxirgi savolni saqlash
        if current_question and current_answers:
            for ans_text, is_correct in current_answers:
                Answer.objects.create(
                    question=current_question,
                    text=ans_text,
                    is_correct=is_correct
                )

        self.stdout.write(self.style.SUCCESS("✅ Import muvaffaqiyatli tugadi!"))