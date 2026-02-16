import sys
try:
    from pypdf import PdfReader
    print("pypdf is installed.")
except ImportError:
    try:
        import PyPDF2
        print("PyPDF2 is installed.")
        from PyPDF2 import PdfReader
    except ImportError:
        print("Neither pypdf nor PyPDF2 is installed.")
        sys.exit(1)

pdf_path = "CAD-CAE-CAM_test-uz.pdf"

try:
    reader = PdfReader(pdf_path)
    print(f"Number of pages: {len(reader.pages)}")
    
    # Read first 2 pages
    for i in range(min(2, len(reader.pages))):
        page = reader.pages[i]
        text = page.extract_text()
        print(f"--- Page {i+1} ---")
        print(text)
        print("-----------------")
        
except Exception as e:
    print(f"Error reading PDF: {e}")
