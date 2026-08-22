from processing.document_loader import extract_pdf_text


text = extract_pdf_text("../sample_resume.pdf")

print(text)