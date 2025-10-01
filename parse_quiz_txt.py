from docx import Document

doc = Document("ТЕСТ-1.docx")

for table in doc.tables:
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        print(cells)
