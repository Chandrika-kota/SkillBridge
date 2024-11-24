from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify,send_from_directory
from db_connection import connect_to_db, close_db_connection
from config import DevelopmentConfig
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import requests

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os

# Directory to store the generated certificates
CERTIFICATE_DIR = os.path.join(os.getcwd(), 'static', 'certificates')
QUIZ_API_KEY="wchwzzcJfWcEdcsw5LQjkYqNlBYMduTXUppM90Rf"
# Create the directory if it doesn't exist
if not os.path.exists(CERTIFICATE_DIR):
    os.makedirs(CERTIFICATE_DIR)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
connection = connect_to_db()

@app.route('/')
def home():
    print("Home page started for SKillBridge")
    return render_template('home.html')
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/registration')
def registration():
    return render_template('registration.html')
@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/logout')
def logout():
    session["user_id"]=""
    return render_template('home.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/assesment')
def assesment():
    return render_template('assesment.html')

@app.route('/mentee')
def mentee():
    return render_template('mentee.html')

@app.route('/mentor')
def mentor():
    """
    Displays the Mentor Dashboard with pending training requests and completed trainings.
    If the mentor has no skill with proficiency > 3, shows an appropriate message.
    """
    mentor_id = session.get('user_id')  # Assuming the logged-in mentor's ID is stored in the session
    if not mentor_id:
        return redirect(url_for('login'))

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        # Check if mentor has any skills with proficiency > 3
        skill_check_query = """
        SELECT s.name AS skill_name, us.proficiency
        FROM User_Skills us
        JOIN Skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s AND us.proficiency > 3
        """
        cursor.execute(skill_check_query, (mentor_id,))
        high_proficiency_skills = cursor.fetchall()

        if not high_proficiency_skills:
            return render_template('mentor.html', no_high_proficiency=True)

        # Fetch pending training requests
        pending_requests_query = """
        SELECT 
            mr.request_id, u.username AS mentee_name, s.name AS skill_name, 
            mr.start_date, mr.end_date, mr.start_time, mr.end_time
        FROM Mentor_Requests mr
        JOIN Users u ON mr.mentee_id = u.user_id
        JOIN Skills s ON mr.skill_id = s.skill_id
        WHERE mr.mentor_id = %s AND mr.status = 'Pending'
        """
        cursor.execute(pending_requests_query, (mentor_id,))
        training_requests = cursor.fetchall()

        # Fetch completed trainings
        completed_trainings_query = """
        SELECT 
            mr.request_id, u.username AS mentee_name, s.name AS skill_name, 
            mr.start_date, mr.end_date, mr.certificate_url
        FROM Mentor_Requests mr
        JOIN Users u ON mr.mentee_id = u.user_id
        JOIN Skills s ON mr.skill_id = s.skill_id
        WHERE mr.mentor_id = %s AND mr.status = 'Completed'
        """
        cursor.execute(completed_trainings_query, (mentor_id,))
        completed_trainings = cursor.fetchall()
        # Fetch completed trainings
        ongoing_trainings_query = """
        SELECT 
            mr.request_id, u.username AS mentee_name, s.name AS skill_name, 
            mr.start_date, mr.end_date, mr.certificate_url
        FROM Mentor_Requests mr
        JOIN Users u ON mr.mentee_id = u.user_id
        JOIN Skills s ON mr.skill_id = s.skill_id
        WHERE mr.mentor_id = %s AND mr.status = 'Approved'
        """
        cursor.execute(ongoing_trainings_query, (mentor_id,))
        ongoing_trainings = cursor.fetchall()

    except Exception as e:
        flash(f"Error loading dashboard: {e}", "error")
        training_requests = []
        completed_trainings = []
    finally:
        cursor.close()
        connection.close()

    return render_template(
        'mentor.html',
        no_high_proficiency=False,
        training_requests=training_requests,
        completed_trainings=completed_trainings,
        ongoing_trainings=ongoing_trainings
    )
@app.route('/approve_training/<int:request_id>', methods=['GET'])
def approve_training(request_id):
    """
    Approves a training request by updating its status to 'Approved' and setting the start date.
    """
    connection = connect_to_db()
    cursor = connection.cursor()

    try:
        # Update the training request to 'Approved'
        update_query = """
        UPDATE Mentor_Requests
        SET status = 'Approved', start_date = NOW()
        WHERE request_id = %s
        """
        cursor.execute(update_query, (request_id,))
        
        connection.commit()

        flash("Training request approved successfully!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Error approving training request: {e}", "error")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('mentor'))
@app.route('/complete_training/<int:request_id>', methods=['GET'])
def complete_training(request_id):
    """
    Marks a training request as 'Completed', generates a certificate, and updates the database.
    """
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch the training request details
        fetch_query = """
        SELECT 
            u.username AS mentee_name, m.username AS mentor_name, 
            s.name AS skill_name, mr.start_date, NOW() AS end_date
        FROM Mentor_Requests mr
        JOIN Users u ON mr.mentee_id = u.user_id
        JOIN Users m ON mr.mentor_id = m.user_id
        JOIN Skills s ON mr.skill_id = s.skill_id
        WHERE mr.request_id = %s
        """
        cursor.execute(fetch_query, (request_id,))
        training_details = cursor.fetchone()

        if not training_details:
            flash("Training request not found.", "error")
            return redirect(url_for('mentor_dashboard'))

        mentee_name = training_details['mentee_name']
        mentor_name = training_details['mentor_name']
        skill_name = training_details['skill_name']
        start_date = training_details['start_date']
        end_date = training_details['end_date']

        # Generate the certificate
        certificate_path = generate_certificate_pdf(
            request_id, mentee_name, mentor_name, skill_name, start_date, end_date
        )

        # Update the training request to 'Completed'
        update_query = """
        UPDATE Mentor_Requests
        SET status = 'Completed', end_date = %s, certificate_url = %s
        WHERE request_id = %s
        """
        cursor.execute(update_query, (end_date, certificate_path, request_id))
        connection.commit()

        flash("Training marked as completed!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Error completing training: {e}", "error")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('mentor'))

# def generate_certificate_pdf(request_id, mentee_name, mentor_name, skill_name, start_date, end_date):
#     """
#     Generate a certificate for the completed training session.

#     :param request_id: The training request ID.
#     :param mentee_name: The name of the mentee.
#     :param mentor_name: The name of the mentor.
#     :param skill_name: The name of the skill.
#     :param start_date: The start date of the training.
#     :param end_date: The end date of the training.
#     :return: The file path of the generated certificate.
#     """
#     certificate_filename = f'{request_id}.pdf'
#     certificate_path = os.path.join(CERTIFICATE_DIR, certificate_filename)

#     c = canvas.Canvas(certificate_path, pagesize=letter)
#     width, height = letter

#     # Title
#     c.setFont("Helvetica-Bold", 24)
#     c.drawString(100, height - 100, "Certificate of Training Completion")

#     # Mentor & Mentee Details
#     c.setFont("Helvetica", 12)
#     c.drawString(100, height - 150, f"This certifies that {mentee_name}")
#     c.drawString(100, height - 170, f"has successfully completed the training on:")
#     c.drawString(100, height - 190, f"Skill: {skill_name}")

#     # Training Dates
#     c.drawString(100, height - 230, f"Start Date: {start_date}")
#     c.drawString(100, height - 250, f"End Date: {end_date}")

#     # Mentor Details
#     c.drawString(100, height - 290, f"Mentor: {mentor_name}")

#     # Footer
#     c.setFont("Helvetica-Bold", 10)
#     c.drawString(100, height - 320, f"Training Request ID: {request_id}")

#     c.showPage()
#     c.save()

#     return certificate_path


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

@app.route('/loginOp', methods=['GET', 'POST'])
def loginOp():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection = connect_to_db()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT * FROM Users WHERE username = %s"
                cursor.execute(query, (username,))
                user = cursor.fetchone()

                if user and user['password']==password:
                    session['user_id'] = user['user_id']  # Store user ID in session
                    flash("Login successful!", "success")
                    return redirect(url_for('home'))
                else:
                    flash("Invalid username or password.", "error")
            except Exception as e:
                print(f"Error during login: {e}")
                flash("An error occurred. Please try again.", "error")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed.", "error")

    return render_template('login.html')


@app.route('/registrationOp', methods=['GET', 'POST'])
def registrationOp():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')  # Plaintext password
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        skills = request.form.get('skills-selected')

        # Validate passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template('registration.html')

        if connection:
            try:
                cursor = connection.cursor()
                # Check if username or email already exists
                query = "SELECT * FROM Users WHERE username = %s OR email = %s"
                cursor.execute(query, (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash("Username or Email already exists.", "error")
                    return render_template('registration.html')

                # Insert user into the database
                insert_user_query = """
                INSERT INTO Users (username, email, password, created_at, updated_at) 
                VALUES (%s, %s, %s, NOW(), NOW())
                """
                cursor.execute(insert_user_query, (username, email, password))
                user_id = cursor.lastrowid
                # connection.commit()
                skills_dict={}
                skills=json.loads(skills)
                for i in skills:
                    skills_dict[i["name"]]=i["proficiency"]
                # Add skills if provided
                if skills:
                    skill_list = skills_dict.keys()  # Assuming skills are comma-separated
                    for skill in skill_list:
                        # Insert or update skills in the Skills table
                        check_skill_query = "SELECT skill_id FROM Skills WHERE name = %s"
                        cursor.execute(check_skill_query, (skill.strip(),))
                        skill_record = cursor.fetchone()

                        if skill_record:
                            skill_id = skill_record[0]
                        else:
                            insert_skill_query = "INSERT INTO Skills (name) VALUES (%s)"
                            cursor.execute(insert_skill_query, (skill.strip(),))
                            skill_id = cursor.lastrowid

                        # Link user to skills in User_Skills table
                        insert_user_skill_query = """
                        INSERT INTO User_Skills (user_id, skill_id, proficiency, last_assessed) 
                        VALUES (%s, %s, %s, NOW())
                        """
                        cursor.execute(insert_user_skill_query, (user_id, skill_id, skills_dict[skill]))

                connection.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))

            except Exception as e:
                print(f"Error during registration: {e}")
                flash("An error occurred. Please try again.", "error")
                connection.rollback()
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed.", "error")

@app.route('/forgot_passwordOp', methods=['GET', 'POST'])
def forgot_passwordOp():
    if request.method == 'POST':
        # Password reset logic here
        flash('Password reset link sent to your email!', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/get_skills', methods=['GET'])
def get_skills():
    query = request.args.get('query', '')
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name FROM Skills WHERE name LIKE %s", (f"%{query}%",))
    skills = cursor.fetchall()
    cursor.close()
    return jsonify(skills)

@app.route('/search_mentors', methods=['GET'])
def search_mentors():
    skill_name = request.args.get('skill', '')
    cursor = connection.cursor(dictionary=True)
    # Fetch mentors proficient in the skill (> 3 proficiency)
    query = """    SELECT u.user_id, u.username, s.name as skill, us.proficiency, us.skill_id as skill_id   FROM Users u    JOIN User_Skills us ON u.user_id = us.user_id    JOIN Skills s ON us.skill_id = s.skill_id    WHERE s.name LIKE %s AND us.proficiency > 3"""
    cursor.execute(query, (f"%{skill_name}%",))
    mentors=cursor.fetchall()
    for mentor in mentors:
        if mentor["user_id"] == session["user_id"]:
            mentors.remove(mentor)
    
    return jsonify(mentors)
@app.route('/top_skills', methods=['GET'])
def top_skills():
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT s.name AS skill, AVG(us.proficiency) AS avg_proficiency
    FROM User_Skills us
    JOIN Skills s ON us.skill_id = s.skill_id
    GROUP BY s.skill_id
    ORDER BY avg_proficiency DESC
    LIMIT 5
    """
    cursor.execute(query)
    top_skills=cursor.fetchall()
    for i in top_skills:
        i["avg_proficiency"]=round(i["avg_proficiency"], 2)
    return jsonify(top_skills)
@app.route('/request_training', methods=['POST'])
def request_training():
    """
    API to handle training requests from mentees to mentors.
    Inserts the training request into the Mentor_Requests table.
    """
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    mentee_id = session.get('user_id')  # Ensure mentee is logged in
    mentor_id = request.form.get('mentor_id')
    skill_id = request.form.get('skill_id')
    start_date = request.form.get('start_date')  # Start date of the training
    end_date = request.form.get('end_date')  # End date of the training
    start_time = request.form.get('start_time')  # Start time of the training
    end_time = request.form.get('end_time')  # End time of the training

    # Validate user login
    if not mentee_id:
        return jsonify({'error': 'User not logged in.'}), 401

    # Validate input data
    if not all([mentor_id, skill_id, start_date, end_date, start_time, end_time]):
        return jsonify({'error': 'All fields are required.'}), 400

    try:
        # Check if the date range is valid (max 10 days)
        date_diff = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        if date_diff < 0 or date_diff > 10:
            return jsonify({'error': 'Date range must be within 10 days.'}), 400

        # Check if the time slot is valid (max 2 hours)
        time_diff = (
            datetime.strptime(end_time, "%H:%M") - datetime.strptime(start_time, "%H:%M")
        ).seconds / 3600
        if time_diff <= 0 or time_diff > 2:
            return jsonify({'error': 'Time slot must not exceed 2 hours.'}), 400

        # Insert training request into the database
        query = """
        INSERT INTO Mentor_Requests (mentee_id, mentor_id, skill_id, start_date, end_date, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
        """
        cursor.execute(query, (mentee_id, mentor_id, skill_id, start_date, end_date, start_time, end_time))
        connection.commit()

        return jsonify({'message': 'Training request sent successfully!'}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': f'Error sending training request: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()
@app.route('/get_requested_trainings', methods=['GET'])
def get_requested_trainings():
    """
    Fetches all training requests made by the logged-in mentee, including their status.
    """
    mentee_id = session.get('user_id')  # Ensure mentee is logged in
    if not mentee_id:
        return jsonify({'error': 'User not logged in.'}), 401

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch training requests for the mentee
        query = """
        SELECT 
            mr.start_date, mr.end_date, mr.status,
            s.name AS skill_name,
            u.username AS mentor_name
        FROM Mentor_Requests mr
        JOIN Skills s ON mr.skill_id = s.skill_id
        JOIN Users u ON mr.mentor_id = u.user_id
        WHERE mr.mentee_id = %s
        ORDER BY mr.start_date DESC
        """
        cursor.execute(query, (mentee_id,))
        training_requests = cursor.fetchall()

        return jsonify(training_requests), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching requested trainings: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# @app.route('/view_profile', methods=['GET'])
# def view_profile():
#     """
#     Render the user profile page.
#     """
#     user_id = session.get('user_id')
#     if not user_id:
#         return redirect(url_for('login'))

#     connection = connect_to_db()
#     cursor = connection.cursor(dictionary=True)

#     try:
#         query = "SELECT * FROM Users WHERE user_id = %s"
#         cursor.execute(query, (user_id,))
#         user_data = cursor.fetchone()
#     finally:
#         cursor.close()
#         connection.close()

#     return render_template('view_profile.html', user=user_data)

@app.route('/view_profile', methods=['GET'])
def view_profile():
    """
    Render the user profile page with skills and proficiencies.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch user details
        query_user = "SELECT username, email FROM Users WHERE user_id = %s"
        cursor.execute(query_user, (user_id,))
        user_data = cursor.fetchone()

        # Fetch skills and proficiencies
        query_skills = """
        SELECT s.name, us.proficiency 
        FROM User_Skills us
        INNER JOIN Skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        """
        cursor.execute(query_skills, (user_id,))
        user_skills = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template('view_profile.html', user=user_data, skills=user_skills)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """
    Handle user profile editing.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        try:
            query = "UPDATE Users SET username = %s, email = %s WHERE user_id = %s"
            cursor.execute(query, (username, email, user_id))
            connection.commit()
            flash("Profile updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating profile: {e}", "error")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('view_profile'))

    # Fetch current user data
    query = "SELECT * FROM Users WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()

    return render_template('edit_profile.html', user=user_data)
@app.route('/view_certificates', methods=['GET'])
def view_certificates():
    """
    Show the list of certificates for the logged-in user.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT mr.certificate_url, s.name AS skill_name, mr.end_date
        FROM Mentor_Requests mr
        JOIN Skills s ON mr.skill_id = s.skill_id
        WHERE mr.mentee_id = %s AND mr.status = 'Completed'
        """
        
        cursor.execute(query, (user_id,))
        certificates = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template('view_certificates.html', certificates=certificates)
import os
from flask import send_file, abort

@app.route('/download_certificate')
def download_certificate():
    """
    Allows downloading of a certificate file.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    certificate_url = request.args.get('certificate_url')
    if not certificate_url:
        abort(400, "Certificate URL is required")

    # Validate that the user owns the certificate
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT certificate_url
        FROM Mentor_Requests
        WHERE certificate_url = %s AND mentee_id = %s
        """
        cursor.execute(query, (certificate_url, user_id))
        result = cursor.fetchone()
        if not result:
            abort(403, "Unauthorized access to certificate")

        # Serve the file
        file_path = os.path.join('static', 'certificates', certificate_url)
        return send_file(file_path, as_attachment=True)

    finally:
        cursor.close()
        connection.close()
@app.route('/get_user_skills', methods=['GET'])
def get_user_skills():
    """
    Fetch the skills registered for the logged-in user.
    """
    user_id = session.get('user_id')  # Assume user is logged in
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT s.name
        FROM User_Skills us
        JOIN Skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s;
    """
    cursor.execute(query, (user_id,))
    skills = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(skills)


@app.route('/fetch_questions/<string:skill_name>', methods=['GET'])
def fetch_questions(skill_name):
    """
    Fetch 10 questions for the selected skill from QuizAPI.
    """
    try:
        # Fetch questions from QuizAPI
        response = requests.get(
            "https://quizapi.io/api/v1/questions",
            headers={"X-Api-Key": QUIZ_API_KEY},
            params={"tags": skill_name, "limit": 10}
        )
        questions = response.json()
        if "error" in questions:
            return jsonify({"questions":[]})
        # Transform questions for frontend compatibility
        formatted_questions = [
            {
                "question_id": q["id"],
                "question": q["question"],
                "options": {
                    "A": q["answers"]["answer_a"],
                    "B": q["answers"]["answer_b"],
                    "C": q["answers"]["answer_c"],
                    "D": q["answers"]["answer_d"]
                },
                "correct_option": next(
                    (key.split("_")[1].split("_")[0] for key, value in q["correct_answers"].items() if value == "true"), None
                )
            }
            for q in questions if q["answers"]["answer_a"]
        ]

        return jsonify({"questions": formatted_questions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    """
    Calculates the user's score and assigns a grade.
    """
    data = request.json
    skill_name=data["skillId"]
    user_answers = data["answers"]  # Format: {'question_id': 'A', ...}
    questions = data["questions"]   # Contains correct answers

    # Calculate score
    score = sum(
        1 for q in questions
        if user_answers.get(str(q["question_id"])).lower() == q["correct_option"].lower()
    )

    # Assign grade
    if score >= 9:
        grade = 5  # Expert
    elif score >= 7:
        grade = 4  # Advanced
    elif score >= 5:
        grade = 3  # Intermediate
    elif score >= 3:
        grade = 2  # Beginner
    else:
        grade = 1  # Novice
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    try:
        # Get skill_id for the given skill_name
        cursor.execute("SELECT skill_id FROM Skills WHERE name = %s", (skill_name,))
        skill = cursor.fetchone()

        if not skill:
            return jsonify({"error": f"Skill {skill_name} not found"}), 404

        skill_id = skill["skill_id"]

        # Check if the user already has the skill
        cursor.execute(
            "SELECT user_skill_id FROM User_Skills WHERE user_id = %s AND skill_id = %s",
            (session["user_id"], skill_id)
        )
        user_skill = cursor.fetchone()

        if user_skill:
            # Update the existing record
            update_query = """
            UPDATE User_Skills
            SET proficiency = %s, last_assessed = NOW()
            WHERE user_skill_id = %s
            """
            cursor.execute(update_query, (score, user_skill["user_skill_id"]))
        else:
            # Insert a new record
            insert_query = """
            INSERT INTO User_Skills (user_id, skill_id, proficiency, last_assessed)
            VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (session["user_id"], skill_id, score))

        connection.commit()
        return jsonify({"score": score, "grade": grade}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
