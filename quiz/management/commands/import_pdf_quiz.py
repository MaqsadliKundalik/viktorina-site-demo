from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from PyPDF2 import PdfReader
import re

class Command(BaseCommand):
    help = "PDF fayldan testlarni import qiladi (savollar ++++ bilan, javoblar ==== bilan ajratilgan)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="PDF fayl yo'li")

    def handle(self, *args, **options):
        filepath = options["filepath"]

        try:
            reader = PdfReader(filepath)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"PDF o'qishda xatolik: {e}"))
            return

        base_category_name = "CAD-CAE-CAM Testlari"
        base_quiz_title = "CAD-CAE-CAM Quiz"
        category_counter = 1

        # Kategoriya yaratish
        current_category, _ = Category.objects.get_or_create(
            name=f"{base_category_name} {category_counter}"
        )
        current_quiz, _ = Quiz.objects.get_or_create(
            title=f"{base_quiz_title} {category_counter}",
            category=current_category
        )

        # Savollarni ajratib olish (++++ bilan)
        raw_questions = full_text.split("++++")
        
        imported = 0

        for raw_q in raw_questions:
            raw_q = raw_q.strip()
            if not raw_q:
                continue

            # Javoblarni ajratish (==== bilan)
            parts = raw_q.split("====")
            
            # Agar savol va kamida bitta javob bo'lmasa, o'tkazib yuboramiz
            if len(parts) < 2:
                continue

            question_text = parts[0].strip()
            # Ba'zan savol matni oldingi savolning qoldig'i yoki keraksiz belgilar bilan boshlanishi mumkin, tozalaymiz
            # Bu yerda maxsus tozalash kerak bo'lsa qo'shish mumkin
            
            raw_answers = parts[1:]
            
            # Agar savollar soni 50 dan oshsa, yangi kategoriya ochamiz
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

            # Javoblarni saqlash
            for ans_text in raw_answers:
                ans_text = ans_text.strip()
                if not ans_text:
                    continue
                
                is_correct = False
                if ans_text.startswith("#"):
                    is_correct = True
                    ans_text = ans_text[1:].strip() # # belgisini olib tashlaymiz
                
                Answer.objects.create(
                    question=current_question,
                    text=ans_text,
                    is_correct=is_correct
                )
            
            imported += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi! {imported} ta savol qo'shildi."))
