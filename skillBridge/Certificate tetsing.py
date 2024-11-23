
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os

CERTIFICATE_DIR = "static/certificates"

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

CERTIFICATE_DIR = "static/certificates"

def generate_certificate_pdf(request_id, mentee_name, mentor_name, skill_name, start_date, end_date):
    """
    Generate a certificate for the completed training session with a full-page background.

    :param request_id: The training request ID.
    :param mentee_name: The name of the mentee.
    :param mentor_name: The name of the mentor.
    :param skill_name: The name of the skill.
    :param start_date: The start date of the training.
    :param end_date: The end date of the training.
    :return: The file path of the generated certificate.
    """
    certificate_filename = f'{request_id}.pdf'
    certificate_path = os.path.join(CERTIFICATE_DIR, certificate_filename)

    if not os.path.exists(CERTIFICATE_DIR):
        os.makedirs(CERTIFICATE_DIR)

    c = canvas.Canvas(certificate_path, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Full-page Background Image
    background_image = ImageReader('static/images/certificateBackground.jpg')
    c.drawImage(background_image, 0, 0, width=width, height=height)
# Logo at Top-Left
    logo_image = ImageReader('static/images/logo.jpeg')
    c.drawImage(logo_image, 50, height - 100, width=100, height=50)

    # Title
    c.setFont("Helvetica-Bold", 32)
    c.setFillColorRGB(0.2, 0.4, 0.6)  # Deep gray-blue
    c.drawCentredString(width / 2, height - 100, "Certificate of Training Completion")

    # Mentee Details
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, height - 160, f"This is to certify that")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 200, mentee_name)

    # Skill Name
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 240, f"has successfully completed training in:")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.2, 0.4, 0.6)
    c.drawCentredString(width / 2, height - 280, skill_name)

    # Training Dates
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, height - 320, f"Training Period: {start_date} to {end_date}")

    # Mentor Details
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 360, f"Mentor: {mentor_name}")

    # Footer with Request ID
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, height - 400, f"Training Request ID: {request_id}")

    c.save()

    return certificate_path

def test_generate_certificate():
    # Test data
    request_id = 19
    mentee_name = "John Doe"
    mentor_name = "Jane Smith"
    skill_name = "Python Programming"
    start_date = "2023-01-01"
    end_date = "2023-01-10"

    # Generate the certificate
    certificate_path = generate_certificate_pdf(
        request_id=request_id,
        mentee_name=mentee_name,
        mentor_name=mentor_name,
        skill_name=skill_name,
        start_date=start_date,
        end_date=end_date
    )

    # Print success message
    if os.path.exists(certificate_path):
        print(f"Certificate successfully generated at: {certificate_path}")
    else:
        print("Failed to generate the certificate.")

# Run the test
if __name__ == "__main__":
    test_generate_certificate()
