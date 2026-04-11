from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import MedicalRecord, LabReport
from accounts.models import User
from appointments.models import Appointment


@login_required
def medical_record_list_view(request):
    if request.user.is_admin:
        medical_records = MedicalRecord.objects.select_related('patient', 'doctor').order_by('-created_at')
    elif request.user.is_doctor:
        medical_records = MedicalRecord.objects.filter(doctor=request.user).select_related('patient').order_by('-created_at')
    else:
        medical_records = MedicalRecord.objects.filter(patient=request.user).select_related('doctor').order_by('-created_at')
    return render(request, 'medical_records/medical_record_list.html', {'medical_records': medical_records})

@login_required
def medical_record_detail_view(request, record_id):
    try:
        medical_record = MedicalRecord.objects.get(id=record_id)
        
        # Check permissions
        if request.user.is_admin:
            # Admin can see all records
            pass
        elif request.user.is_doctor:
            # Doctor can only see their own records
            if medical_record.doctor != request.user:
                messages.error(request, 'Access denied! You can only view your own medical records.')
                return redirect('medical_records:medical_record_list')
        else:
            # Patient can only see their own records
            if medical_record.patient != request.user:
                messages.error(request, 'Access denied! You can only view your own medical records.')
                return redirect('medical_records:medical_record_list')
        
        return render(request, 'medical_records/medical_record_detail.html', {'medical_record': medical_record})
        
    except MedicalRecord.DoesNotExist:
        messages.error(request, 'Medical record not found!')
        return redirect('medical_records:medical_record_list')

@login_required
def create_medical_record_view(request):
    if request.user.is_patient:
        messages.error(request, 'Access denied! Only doctors and admins can create medical records.')
        return redirect('medical_records:medical_record_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            doctor_id = request.POST.get('doctor')
            appointment_id = request.POST.get('appointment')
            chief_complaint = request.POST.get('chief_complaint')
            history_of_present_illness = request.POST.get('history_of_present_illness', '')
            past_medical_history = request.POST.get('past_medical_history', '')
            physical_examination = request.POST.get('physical_examination', '')
            assessment = request.POST.get('assessment')
            plan = request.POST.get('plan')
            is_confidential = request.POST.get('is_confidential') == 'on'
            
            # Get objects
            patient = User.objects.get(id=patient_id)
            doctor = User.objects.get(id=doctor_id) if doctor_id else request.user
            appointment = Appointment.objects.get(id=appointment_id) if appointment_id else None
            
            # Create medical record
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                doctor=doctor,
                appointment=appointment,
                chief_complaint=chief_complaint,
                history_of_present_illness=history_of_present_illness or None,
                past_medical_history=past_medical_history or None,
                physical_examination=physical_examination or None,
                assessment=assessment,
                plan=plan,
                is_confidential=is_confidential
            )
            
            messages.success(request, f'Medical record for {patient.get_full_name()} created successfully!')
            return redirect('medical_records:medical_record_list')
            
        except Exception as e:
            messages.error(request, f'Error creating medical record: {str(e)}')
    
    # Get context data for form
    context = {}
    
    if request.user.is_admin:
        # Admin can see all patients and doctors
        context['patients'] = User.objects.filter(role='patient', is_active=True)
        context['doctors'] = User.objects.filter(role='doctor', is_active=True)
        context['appointments'] = Appointment.objects.filter(status='confirmed')
    elif request.user.is_doctor:
        # Doctor can only see their patients and appointments
        context['patients'] = User.objects.filter(role='patient', is_active=True)
        context['appointments'] = Appointment.objects.filter(doctor=request.user, status='confirmed')
    
    return render(request, 'medical_records/create_medical_record.html', context)

@login_required
def update_medical_record_view(request, record_id):
    try:
        medical_record = MedicalRecord.objects.get(id=record_id)
        
        # Check permissions
        if request.user.is_admin:
            # Admin can edit all records
            pass
        elif request.user.is_doctor:
            # Doctor can only edit their own records
            if medical_record.doctor != request.user:
                messages.error(request, 'Access denied! You can only edit your own medical records.')
                return redirect('medical_records:medical_record_list')
        else:
            # Patients cannot edit records
            messages.error(request, 'Access denied! Only doctors and admins can edit medical records.')
            return redirect('medical_records:medical_record_list')
        
        if request.method == 'POST':
            try:
                # Get form data
                appointment_id = request.POST.get('appointment')
                chief_complaint = request.POST.get('chief_complaint')
                history_of_present_illness = request.POST.get('history_of_present_illness', '')
                past_medical_history = request.POST.get('past_medical_history', '')
                family_history = request.POST.get('family_history', '')
                social_history = request.POST.get('social_history', '')
                physical_examination = request.POST.get('physical_examination', '')
                assessment = request.POST.get('assessment')
                plan = request.POST.get('plan')
                is_confidential = request.POST.get('is_confidential') == 'on'
                
                # Get vital signs
                vital_signs = {}
                blood_pressure = request.POST.get('blood_pressure')
                heart_rate = request.POST.get('heart_rate')
                respiratory_rate = request.POST.get('respiratory_rate')
                temperature = request.POST.get('temperature')
                oxygen_saturation = request.POST.get('oxygen_saturation')
                
                if blood_pressure:
                    vital_signs['blood_pressure'] = blood_pressure
                if heart_rate:
                    vital_signs['heart_rate'] = int(heart_rate)
                if respiratory_rate:
                    vital_signs['respiratory_rate'] = int(respiratory_rate)
                if temperature:
                    vital_signs['temperature'] = float(temperature)
                if oxygen_saturation:
                    vital_signs['oxygen_saturation'] = int(oxygen_saturation)
                
                # Update medical record
                medical_record.appointment = Appointment.objects.get(id=appointment_id) if appointment_id else None
                medical_record.chief_complaint = chief_complaint
                medical_record.history_of_present_illness = history_of_present_illness or None
                medical_record.past_medical_history = past_medical_history or None
                medical_record.family_history = family_history or None
                medical_record.social_history = social_history or None
                medical_record.physical_examination = physical_examination or None
                medical_record.assessment = assessment
                medical_record.plan = plan
                medical_record.is_confidential = is_confidential
                medical_record.vital_signs = vital_signs if vital_signs else None
                medical_record.save()
                
                messages.success(request, f'Medical record for {medical_record.patient.get_full_name()} updated successfully!')
                return redirect('medical_records:medical_record_detail', record_id=medical_record.id)
                
            except Exception as e:
                messages.error(request, f'Error updating medical record: {str(e)}')
        
        # Get context data for form
        context = {'medical_record': medical_record}
        
        if request.user.is_admin:
            # Admin can see all appointments
            context['appointments'] = Appointment.objects.filter(status='confirmed')
        elif request.user.is_doctor:
            # Doctor can only see their appointments
            context['appointments'] = Appointment.objects.filter(doctor=request.user, status='confirmed')
        
        return render(request, 'medical_records/update_medical_record.html', context)
        
    except MedicalRecord.DoesNotExist:
        messages.error(request, 'Medical record not found!')
        return redirect('medical_records:medical_record_list')

@login_required
def lab_report_list_view(request):
    user = request.user
    if user.is_admin:
        lab_reports = LabReport.objects.select_related('patient', 'doctor').order_by('-ordered_date')
    elif user.is_doctor:
        lab_reports = (
            LabReport.objects.filter(doctor=user)
            .select_related('patient', 'doctor')
            .order_by('-ordered_date')
        )
    else:
        # Patients only see their own lab reports
        lab_reports = (
            LabReport.objects.filter(patient=user)
            .select_related('patient', 'doctor')
            .order_by('-ordered_date')
        )

    # Calculate statistics (on the scoped queryset)
    total_reports = lab_reports.count()
    completed_reports = lab_reports.filter(status='completed').count()
    in_progress_reports = lab_reports.filter(status='in_progress').count()
    pending_reports = lab_reports.filter(status='pending').count()
    
    context = {
        'lab_reports': lab_reports,
        'total_reports': total_reports,
        'completed_reports': completed_reports,
        'in_progress_reports': in_progress_reports,
        'pending_reports': pending_reports,
    }
    
    return render(request, 'medical_records/lab_report_list.html', context)

@login_required
def lab_report_detail_view(request, report_id):
    user = request.user
    base = LabReport.objects.select_related('patient', 'doctor', 'patient__patient_profile', 'doctor__doctor_profile')
    if user.is_admin:
        lab_report = get_object_or_404(base, id=report_id)
    elif user.is_doctor:
        lab_report = get_object_or_404(base, id=report_id, doctor=user)
    else:
        lab_report = get_object_or_404(base, id=report_id, patient=user)

    return render(request, 'medical_records/lab_report_detail.html', {'lab_report': lab_report})

@login_required
def create_lab_report_view(request):
    if request.user.is_patient:
        messages.error(request, 'Access denied! Only doctors and admins can create lab reports.')
        return redirect('medical_records:lab_report_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            doctor_id = request.POST.get('doctor')
            report_type = request.POST.get('report_type')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            results = request.POST.get('results', '')
            status = request.POST.get('status', 'pending')
            report_file = request.FILES.get('report_file')
            
            # Get objects
            patient = User.objects.get(id=patient_id)
            doctor = User.objects.get(id=doctor_id) if doctor_id else request.user
            
            # Create lab report
            lab_report = LabReport.objects.create(
                patient=patient,
                doctor=doctor,
                report_type=report_type,
                title=title,
                description=description or None,
                results=results or None,
                status=status,
                report_file=report_file
            )
            
            messages.success(request, f'Lab report "{lab_report.title}" for {patient.get_full_name()} created successfully!')
            return redirect('medical_records:lab_report_list')
            
        except Exception as e:
            messages.error(request, f'Error creating lab report: {str(e)}')
    
    # Get context data for form
    context = {}
    
    if request.user.is_admin:
        # Admin can see all patients and doctors
        context['patients'] = User.objects.filter(role='patient', is_active=True)
        context['doctors'] = User.objects.filter(role='doctor', is_active=True)
    elif request.user.is_doctor:
        # Doctor can see all patients
        context['patients'] = User.objects.filter(role='patient', is_active=True)
    
    return render(request, 'medical_records/create_lab_report.html', context)

@login_required
def edit_lab_report_view(request, report_id):
    user = request.user
    base = LabReport.objects.select_related('patient', 'doctor')
    if user.is_admin:
        lab_report = get_object_or_404(base, id=report_id)
    elif user.is_doctor:
        lab_report = get_object_or_404(base, id=report_id, doctor=user)
    else:
        messages.error(request, 'Access denied! Only doctors and admins can edit lab reports.')
        return redirect('medical_records:lab_report_list')

    if request.method == 'POST':
        try:
            lab_report.report_type = request.POST.get('report_type')
            lab_report.title = request.POST.get('title')
            lab_report.description = request.POST.get('description', '')
            lab_report.results = request.POST.get('results', '')
            lab_report.status = request.POST.get('status', 'pending')

            new_file = request.FILES.get('report_file')
            if new_file:
                lab_report.report_file = new_file

            lab_report.save()
            messages.success(request, f'Lab report "{lab_report.title}" updated successfully!')
            return redirect('medical_records:lab_report_detail', report_id=lab_report.id)

        except Exception as e:
            messages.error(request, f'Error updating lab report: {str(e)}')

    context = {
        'lab_report': lab_report,
        'is_edit': True,
    }
    return render(request, 'medical_records/edit_lab_report.html', context)

@login_required
def upload_lab_report_view(request, report_id):
    user = request.user
    base = LabReport.objects.select_related('patient', 'doctor')
    if user.is_admin:
        lab_report = get_object_or_404(base, id=report_id)
    elif user.is_doctor:
        lab_report = get_object_or_404(base, id=report_id, doctor=user)
    else:
        messages.error(request, 'Access denied! Only doctors and admins can upload lab reports.')
        return redirect('medical_records:lab_report_list')

    return render(request, 'medical_records/upload_lab_report.html', {'lab_report': lab_report})

@login_required
def vital_signs_list_view(request):
    # Get vital signs from medical records that have vital signs data
    if request.user.is_admin:
        medical_records = MedicalRecord.objects.filter(vital_signs__isnull=False).select_related('patient').order_by('-created_at')
    elif request.user.is_doctor:
        medical_records = MedicalRecord.objects.filter(doctor=request.user, vital_signs__isnull=False).select_related('patient').order_by('-created_at')
    else:
        medical_records = MedicalRecord.objects.filter(patient=request.user, vital_signs__isnull=False).select_related('doctor').order_by('-created_at')
    
    # Convert to vital signs format
    vital_signs = []
    for record in medical_records:
        # Start with base data
        vital_data = {
            'patient': record.patient,
            'doctor': record.doctor,
            'recorded_at': record.created_at,
            'medical_record_id': record.id
        }
        
        # Flatten vital signs from JSONField if it exists
        if record.vital_signs:
            vital_data.update(record.vital_signs)
            
            # Ensure measurement_time exists for template and is a datetime object
            if 'measurement_time' in vital_data and isinstance(vital_data['measurement_time'], str):
                try:
                    from django.utils.dateparse import parse_datetime
                    vital_data['measurement_time'] = parse_datetime(vital_data['measurement_time'])
                except:
                    vital_data['measurement_time'] = record.created_at
            
            if not vital_data.get('measurement_time'):
                vital_data['measurement_time'] = record.created_at
        else:
            vital_data['measurement_time'] = record.created_at
            
        vital_signs.append(vital_data)
    
    return render(request, 'medical_records/vital_signs_list.html', {'vital_signs': vital_signs})

@login_required
def add_vital_signs_view(request):
    if request.user.is_patient:
        messages.error(request, 'Access denied! Only doctors and admins can add vital signs.')
        return redirect('medical_records:vital_signs_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            doctor_id = request.POST.get('doctor')
            medical_record_id = request.POST.get('medical_record')
            blood_pressure = request.POST.get('blood_pressure', '')
            heart_rate = request.POST.get('heart_rate', '')
            respiratory_rate = request.POST.get('respiratory_rate', '')
            temperature = request.POST.get('temperature', '')
            oxygen_saturation = request.POST.get('oxygen_saturation', '')
            height = request.POST.get('height', '')
            weight = request.POST.get('weight', '')
            bmi = request.POST.get('bmi', '')
            notes = request.POST.get('clinical_notes', '')
            measurement_time = request.POST.get('measurement_time')
            
            # Get objects
            patient = User.objects.get(id=patient_id)
            doctor = User.objects.get(id=doctor_id) if doctor_id else request.user
            medical_record = MedicalRecord.objects.get(id=medical_record_id) if medical_record_id else None
            
            # Create vital signs data
            vital_signs_data = {}
            if blood_pressure:
                vital_signs_data['blood_pressure'] = blood_pressure
            if heart_rate:
                vital_signs_data['heart_rate'] = int(heart_rate)
            if respiratory_rate:
                vital_signs_data['respiratory_rate'] = int(respiratory_rate)
            if temperature:
                vital_signs_data['temperature'] = float(temperature)
            if oxygen_saturation:
                vital_signs_data['oxygen_saturation'] = int(oxygen_saturation)
            if height:
                vital_signs_data['height'] = float(height)
            if weight:
                vital_signs_data['weight'] = float(weight)
            if bmi:
                vital_signs_data['bmi'] = float(bmi)
            if notes:
                vital_signs_data['notes'] = notes
            if measurement_time:
                vital_signs_data['measurement_time'] = measurement_time
            vital_signs_data['recorded_by'] = doctor.id
            vital_signs_data['recorded_at'] = measurement_time or timezone.now()
            
            # Create or update medical record with vital signs
            if medical_record:
                medical_record.vital_signs = vital_signs_data
                medical_record.save()
                messages.success(request, f'Vital signs for {patient.get_full_name()} updated successfully!')
            else:
                # Create new medical record for vital signs
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=doctor,
                    chief_complaint="Vital signs measurement",
                    assessment="Routine vital signs check",
                    plan="Continue monitoring",
                    vital_signs=vital_signs_data
                )
                messages.success(request, f'Vital signs for {patient.get_full_name()} recorded successfully!')
            
            return redirect('medical_records:vital_signs_list')
            
        except Exception as e:
            messages.error(request, f'Error saving vital signs: {str(e)}')
    
    # Get context data for form
    context = {}
    
    if request.user.is_admin:
        # Admin can see all patients and doctors
        context['patients'] = User.objects.filter(role='patient', is_active=True)
        context['doctors'] = User.objects.filter(role='doctor', is_active=True)
        context['medical_records'] = MedicalRecord.objects.all().order_by('-created_at')[:20]
    elif request.user.is_doctor:
        # Doctor can see all patients and their records
        context['patients'] = User.objects.filter(role='patient', is_active=True)
        context['medical_records'] = MedicalRecord.objects.filter(doctor=request.user).order_by('-created_at')[:20]
    
    return render(request, 'medical_records/add_vital_signs.html', context)

@login_required
def edit_vital_signs_view(request, record_id):
    if request.user.is_patient:
        messages.error(request, 'Access denied! Only doctors and admins can edit vital signs.')
        return redirect('medical_records:vital_signs_list')
    
    try:
        medical_record = MedicalRecord.objects.get(id=record_id)
        
        # Check permissions
        if not request.user.is_admin and medical_record.doctor != request.user:
            messages.error(request, 'Access denied! You can only edit your own recordings.')
            return redirect('medical_records:vital_signs_list')
            
        if request.method == 'POST':
            try:
                # Get form data
                blood_pressure = request.POST.get('blood_pressure', '')
                heart_rate = request.POST.get('heart_rate', '')
                respiratory_rate = request.POST.get('respiratory_rate', '')
                temperature = request.POST.get('temperature', '')
                oxygen_saturation = request.POST.get('oxygen_saturation', '')
                height = request.POST.get('height', '')
                weight = request.POST.get('weight', '')
                bmi = request.POST.get('bmi', '')
                notes = request.POST.get('clinical_notes', '')
                measurement_time = request.POST.get('measurement_time')
                
                # Create vital signs data
                vital_signs_data = {}
                if blood_pressure:
                    vital_signs_data['blood_pressure'] = blood_pressure
                if heart_rate:
                    vital_signs_data['heart_rate'] = int(heart_rate)
                if respiratory_rate:
                    vital_signs_data['respiratory_rate'] = int(respiratory_rate)
                if temperature:
                    vital_signs_data['temperature'] = float(temperature)
                if oxygen_saturation:
                    vital_signs_data['oxygen_saturation'] = int(oxygen_saturation)
                if height:
                    vital_signs_data['height'] = float(height)
                if weight:
                    vital_signs_data['weight'] = float(weight)
                if bmi:
                    vital_signs_data['bmi'] = float(bmi)
                if notes:
                    vital_signs_data['notes'] = notes
                if measurement_time:
                    vital_signs_data['measurement_time'] = measurement_time
                
                # Maintain recorded_by if not admin, or update if admin wants to take over? 
                # Usually keep original recorder but we'll stick to original logic
                vital_signs_data['recorded_by'] = medical_record.doctor.id
                vital_signs_data['recorded_at'] = measurement_time or timezone.now().isoformat()
                
                medical_record.vital_signs = vital_signs_data
                medical_record.save()
                
                messages.success(request, f'Vital signs for {medical_record.patient.get_full_name()} updated successfully!')
                return redirect('medical_records:vital_signs_list')
                
            except Exception as e:
                messages.error(request, f'Error updating vital signs: {str(e)}')
        
        # Prepare data for template
        vital_data = medical_record.vital_signs or {}
        
        context = {
            'medical_record': medical_record,
            'vital_data': vital_data,
        }
        return render(request, 'medical_records/edit_vital_signs.html', context)
        
    except MedicalRecord.DoesNotExist:
        messages.error(request, 'Medical record not found!')
        return redirect('medical_records:vital_signs_list')
