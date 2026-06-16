from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_resume_pdf(filename="test_resume.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, height - 80, "John Doe")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, "Email: tester@test.com")
    c.drawString(100, height - 115, "Phone: +1 555-0199")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 150, "Objective")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 170, "Experienced AI/ML engineer skilled in Python, FastAPI, and machine learning models.")
    c.drawString(100, height - 185, "Interested in building scalable systems using LangChain and LangGraph.")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 220, "Skills")
    
    c.setFont("Helvetica", 10)
    skills = "Python, FastAPI, LangChain, LangGraph, Deep Learning, Machine Learning, AWS, NLP"
    c.drawString(100, height - 240, skills)
    
    c.save()

if __name__ == "__main__":
    create_resume_pdf()
    print("PDF generated successfully.")
