from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Report, db, Log
from app.utils.export_utils import generate_word_report, generate_pdf_report
from datetime import datetime
import os
from werkzeug.utils import secure_filename

report = Blueprint('report', __name__)

@report.route('/submit', methods=['POST'])
@login_required
def submit_report():
    if request.method == 'POST':
        try:
            # Get form data
            source = request.form.get('source')
            title = request.form.get('title')
            post_date = datetime.strptime(request.form.get('post_date'), '%Y-%m-%d')
            summary = request.form.get('summary')
            url = request.form.get('url')
            user_id = request.form.get('user_id')
            
            # Handle file upload
            image = request.files.get('image')
            image_path = None
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
            
            # Get next report number
            last_report = Report.query.filter_by(is_global=True).order_by(Report.report_number.desc()).first()
            report_number = last_report.report_number + 1 if last_report else 1
            
            # Create report
            new_report = Report(
                report_number=report_number,
                source=source,
                title=title,
                post_date=post_date,
                summary=summary,
                url=url,
                user_id=user_id,
                image_path=image_path,
                is_global=False,
                user_id_created=current_user.id
            )
            
            db.session.add(new_report)
            db.session.commit()
            
            # Log the action
            log = Log(
                user_id=current_user.id,
                action=f"Created report {new_report.id}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('user.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting report: {e}")
            flash('Error submitting report. Please try again.', 'danger')
            return redirect(url_for('user.form'))
