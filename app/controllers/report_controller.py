from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app.models import Report, db, Log
from app.utils.export_utils import generate_word_report, generate_pdf_report
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import playsound  # Reproduce sonidos

report = Blueprint('report', __name__)

def allowed_file(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
            
            # Handle file upload
            image = request.files.get('image')
            image_path = None
            if image and not allowed_file(image.filename):
                flash('Archivo no permitido', 'danger')
                return redirect(url_for('user.form'))
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
            
            # Get next report number
            last_report_number = db.session.query(db.func.max(Report.report_number)).scalar() or 0
            report_number = last_report_number + 1
            
            # Create report
            new_report = Report(
                report_number=report_number,
                source=source,
                title=title,
                post_date=post_date,
                summary=summary,
                url=url,
                user_id=current_user.id,  # Fixed user_id to use current_user.id
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
            
        except ValueError as ve:
            db.session.rollback()
            current_app.logger.error(f"ValueError submitting report: {ve}")
            flash('Invalid data format. Please check your inputs.', 'danger')
            return redirect(url_for('user.form'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting report: {e}")
            flash('Error submitting report. Please try again.', 'danger')
            return redirect(url_for('user.form'))

@report.route('/export', methods=['POST'])
@login_required
def export_report():
    try:
        report_id = request.form.get('report_id')
        report = Report.query.get(report_id)
        if not report:
            flash('Report not found', 'danger')
            return redirect(url_for('user.dashboard'))

        output_path = os.path.join(current_app.config['MEDIA_FOLDER'], f'report_{report_id}.pdf')
        generate_pdf_report(report.to_dict(), output_path)

        # Reproduce un sonido al exportar
        sound_path = os.path.join(current_app.config['MEDIA_FOLDER'], 'export_success.mp3')
        if os.path.exists(sound_path):
            playsound.playsound(sound_path)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error exporting report: {e}")
        flash('Error exporting report', 'danger')
        return redirect(url_for('user.dashboard'))
