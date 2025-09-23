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

        # Butun hujjat matnini olish va bo'limlarga ajratish
        full_text = '\n'.join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
        # ++++ bo'yicha bo'limlarga ajratish
        blocks = [block.strip() for block in full_text.split('++++') if block.strip()]

        current_category = None
        current_quiz = None
        category_counter = 1  # Kategoriya nomlari uchun raqam

        # Default category and quiz
        base_category_name = "BOI 2025 Testlari"
        base_quiz_title = "Statistika va Modellashtirish Testlari"

        # Mavjud kategoriyalarni tekshirish uchun
        existing_categories = Category.objects.filter(name__startswith=base_category_name).order_by('name')
        if existing_categories.exists():
            last_category_name = existing_categories.last().name
            match = re.search(r'\d+$', last_category_name)
            if match:
                category_counter = int(match.group()) + 1
            else:
                category_counter = 1

        imported_count = 0

        for block in blocks:
            lines = [line.strip() for line in block.split('\n') if line.strip()]

            if not lines:
                continue

            # Savol matnini olish (birinchi qator)
            question_text = lines[0].strip()
            if not question_text or not question_text.endswith('?'):
                continue  # Savol emas, o'tkazib yuborish

            # Default kategoriya va quiz ni sozlash
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

            # Kategoriyadagi savollar sonini tekshirish va yangi kategoriya yaratish kerak bo'lsa
            question_count = Question.objects.filter(quiz__category=current_category).count()
            if question_count >= 50:
                category_counter += 1
                current_category, _ = Category.objects.get_or_create(name=f"{base_category_name} {category_counter}")
                current_quiz, _ = Quiz.objects.get_or_create(
                    title=f"{base_quiz_title} {category_counter}",
                    category=current_category
                )
                self.stdout.write(self.style.WARNING(f"⚠️ Kategoriya '{current_category.name}'da 50 savoldan oshdi, yangi kategoriya yaratildi: {base_category_name} {category_counter}"))

            # Savol yaratish
            current_question = Question.objects.create(
                quiz=current_quiz,
                text=question_text
            )
            imported_count += 1

            # Javoblarni qayta ishlash (keyingi qatorlar ==== bilan boshlanadi)
            for line in lines[1:]:
                if line.startswith('===='):
                    ans_text = line[4:].strip()  # ==== ni olib tashlash
                    is_correct = False
                    if ans_text.startswith('#'):
                        ans_text = ans_text[1:].strip()  # # ni olib tashlash
                        is_correct = True
                    Answer.objects.create(
                        question=current_question,
                        text=ans_text,
                        is_correct=is_correct
                    )

        self.stdout.write(self.style.SUCCESS(f"✅ Import muvaffaqiyatli tugadi! Jami {imported_count} ta savol import qilindi."))