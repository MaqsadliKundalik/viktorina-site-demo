from docx import Document

def docx_to_txt(docx_path, txt_path):
    # DOCX faylni ochish
    doc = Document(docx_path)

    # Matnlarni yig‘ib olish
    lines = []
    for para in doc.paragraphs:
        if para.text.strip():  # faqat bo'sh bo'lmagan satrlarni olish
            lines.append(para.text)

    # TXT faylga yozish
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Matn '{txt_path}' fayliga yozildi.")

# Foydalanish:
docx_to_txt("BOI_2025_test.docx", "BOI_2025_test.txt")
