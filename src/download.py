# Imports
from io import BytesIO
# Introducing new library to generate and download PDF files - 'reportlab'
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape

def PDF(certificate_image, student_name, course_title, completion_date):
    print(f"Debug inside PDF function: Student Name: {student_name}")
    # Image dimensions
    image_width = 200
    image_height = 200

    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()

    # Custom page size (width, height)
    custom_page_size = (400, 400)

    # Create the PDF object, using the buffer as its "file" and custom page size
    pdf = SimpleDocTemplate(buffer, pagesize=custom_page_size)

    # Create a list to hold the PDF elements
    elements = []

    # Add the certificate image
    certificate_image_path = f"https://ipfs.io/ipfs/{certificate_image}"
    img = Image(certificate_image_path, width=image_width, height=image_height)
    elements.append(img)

    # Define custom style
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'Times-Bold'
    style.fontSize = 14
    style.leading = 12
    style.alignment = TA_CENTER
    style.textColor = colors.black

    # Add student name, course title, and completion date with custom style
    elements.append(Paragraph(f"{student_name}", style))
    elements.append(Paragraph(f"{course_title}", style))
    elements.append(Paragraph(f"{completion_date}", style))

    # Build the PDF
    pdf.build(elements)

    # Move the buffer to the beginning of the file-like object
    buffer.seek(0)

    # Return the buffer
    return buffer







