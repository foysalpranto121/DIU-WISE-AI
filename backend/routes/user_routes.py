from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User

user_bp = Blueprint('user', __name__)

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
    current_user.current_gpa = float(data.get('current_gpa', current_user.current_gpa or 0))
    current_user.credit_load = int(data.get('credit_load', current_user.credit_load or 0))
    
    # Update Goals
    current_user.goals = {
        "study_hours": float(data.get('goal_study_hours', 0)),
        "assignments": int(data.get('goal_assignments', 0))
    }
    
    try:
        db.session.commit()
        flash('Profile and academic settings updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'danger')
        
    return redirect(url_for('user.profile'))
