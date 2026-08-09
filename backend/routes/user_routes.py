from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

user_bp = Blueprint('user', __name__)


class FieldError(ValueError):
    """A submitted field could not be parsed as the number it should be."""


def _as_number(data, field, caster, fallback):
    """Parse one numeric form field, or say which field was wrong.

    FIX: these were bare float()/int() calls on raw form input, so posting
    "abc" as current_gpa raised ValueError and returned a 500.
    """
    raw = data.get(field)
    if raw is None or str(raw).strip() == "":
        return fallback
    try:
        return caster(raw)
    except (TypeError, ValueError):
        raise FieldError(field)

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@user_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.form
    
    current_user.full_name = data.get('full_name', current_user.full_name)
    current_user.university = data.get('university', current_user.university)
    current_user.department = data.get('department', current_user.department)
    current_user.student_id = data.get('student_id', current_user.student_id)
    current_user.phone_number = data.get('phone_number', current_user.phone_number)
    current_user.guardian_name = data.get('guardian_name', current_user.guardian_name)
    current_user.guardian_email = data.get('guardian_email', current_user.guardian_email)
    current_user.guardian_phone = data.get('guardian_phone', current_user.guardian_phone)
    current_user.semester = data.get('semester', current_user.semester)
    current_user.batch = data.get('batch', current_user.batch)
    try:
        current_gpa = _as_number(data, 'current_gpa', float, current_user.current_gpa or 0.0)
        credit_load = _as_number(data, 'credit_load', int, current_user.credit_load or 0)
        goal_study_hours = _as_number(data, 'goal_study_hours', float, 0.0)
        goal_assignments = _as_number(data, 'goal_assignments', int, 0)
    except FieldError as bad_field:
        return jsonify({
            "error": f"'{bad_field}' must be a number",
            "field": str(bad_field),
        }), 400

    current_user.current_gpa = current_gpa
    current_user.credit_load = credit_load

    # Update Goals
    current_user.goals = {
        "study_hours": goal_study_hours,
        "assignments": goal_assignments,
    }

    # Faculty Advisor Alert fields
    current_user.faculty_advisor_email = data.get('faculty_advisor_email', current_user.faculty_advisor_email)
    current_user.advisor_alert_consent = data.get('advisor_alert_consent') == 'on'

    try:
        db.session.commit()
        flash('Profile and academic settings updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'danger')
        
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'profile_picture' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
        # Create uploads folder inside static
        upload_folder = os.path.join(current_app.config['BASE_DIR'], 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        current_user.profile_picture = f"uploads/{filename}"
        db.session.commit()
        
        return jsonify({
            "message": "Profile picture updated successfully!",
            "url": url_for('static', filename=f"uploads/{filename}")
        }), 200
        
    return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400

