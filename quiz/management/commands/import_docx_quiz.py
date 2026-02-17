from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Answer, Category
from docx import Document
import re

class Command(BaseCommand):
    help = "DOCX fayldan testlarni import qiladi (Variant A har doim to'g'ri deb olinadi)"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="DOCX fayl yo'li")

    def handle(self, *args, **options):
        filepath = options["filepath"]
        
        try:
            doc = Document(filepath)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"DOCX o'qishda xatolik: {e}"))
            return

        base_category_name = "ISTAT Sirtqi 5-kurs"
        base_quiz_title = "Ichimlik suv ta'minoti avtomatlashtirish"
        category_counter = 1

        # Kategoriya yaratish
        current_category, _ = Category.objects.get_or_create(
            name=f"{base_category_name} {category_counter}"
        )
        current_quiz, _ = Quiz.objects.get_or_create(
            title=f"{base_quiz_title} {category_counter}",
            category=current_category
        )

        lines = []
        for para in doc.paragraphs:
            if para.text.strip():
                # Split by newlines inside the paragraph just in case
                parts = para.text.strip().split('\n')
                for part in parts:
                    if part.strip():
                        lines.append(part.strip())

        questions_data = []
        current_q_text = []
        current_options = []
        
        # Regex to detect start of options A), B), C), D) or A., B., etc.
        option_pattern = re.compile(r"^([A-D])[\)\.]\s+(.*)")

        for line in lines:
            # Ignore unrelated lines
            if "To‘g‘ri javob:" in line or "fаni bo’yicha nazorat savollari" in line or line.startswith("Ichimlik suv ta’minoti tizimlarini"):
                continue

            match = option_pattern.match(line)
            if match:
                # This is an option line
                opt_letter = match.group(1)
                opt_text = match.group(2).strip()
                current_options.append((opt_letter, opt_text))
            else:
                # This is likely a question line (or continuation of one)
                
                # Check if we were previously collecting options. If so, the PREVIOUS question is finished.
                if current_options:
                    # Save previous question
                    if current_q_text:
                        full_q_text = " ".join(current_q_text).strip()
                        # Remove leading numbers (e.g., "1.", "34.")
                        full_q_text = re.sub(r"^\d+[\.\)]\s*", "", full_q_text)
                        
                        questions_data.append({
                            "text": full_q_text,
                            "options": current_options
                        })
                    
                    # Reset for new question
                    current_q_text = [line]
                    current_options = []
                else:
                    # Still collecting specific question text (multi-line question)
                    current_q_text.append(line)

        # Don't forget the last question
        if current_q_text and current_options:
            full_q_text = " ".join(current_q_text).strip()
            full_q_text = re.sub(r"^\d+[\.\)]\s*", "", full_q_text)
            questions_data.append({
                "text": full_q_text,
                "options": current_options
            })

        self.stdout.write(f"Topilgan savollar soni: {len(questions_data)}")

        imported = 0
        for q_data in questions_data:
            # Check question limit per quiz (50)
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

            question = Question.objects.create(
                quiz=current_quiz,
                text=q_data["text"]
            )
            
            for opt_letter, opt_text in q_data["options"]:
                # Assume A is always correct based on analysis
                is_correct = (opt_letter.upper() == 'A')
                Answer.objects.create(
                    question=question,
                    text=opt_text,
                    is_correct=is_correct
                )
            imported += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi! {imported} ta savol qo'shildi."))
