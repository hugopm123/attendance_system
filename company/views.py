# company/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Avg
from .models import Company, Employee, Attendance
from .serializers import CompanySerializer, EmployeeSerializer, AttendanceSerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=True, methods=['GET'])
    def statistics(self, request, pk=None):
        company = self.get_object()
        total_employees = Employee.objects.filter(company=company).count()
        
        # Calcular asistencia del día actual
        from django.utils import timezone
        today = timezone.now().date()
        present_today = Attendance.objects.filter(
            employee__company=company,
            date=today,
            is_present=True
        ).count()
        
        # Calcular promedio de asistencia del último mes
        last_month = today - timezone.timedelta(days=30)
        avg_attendance = Attendance.objects.filter(
            employee__company=company,
            date__gte=last_month,
            is_present=True
        ).values('date').annotate(
            daily_attendance=Count('id')
        ).aggregate(avg_attendance=Avg('daily_attendance'))

        return Response({
            'company_name': company.name,
            'total_employees': total_employees,
            'present_today': present_today,
            'average_monthly_attendance': avg_attendance['avg_attendance'] or 0
        })

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    @action(detail=False, methods=['GET'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            employees = Employee.objects.filter(company_id=company_id)
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id is required"}, status=status.HTTP_400_BAD_REQUEST)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def create(self, request, *args, **kwargs):
        employee_id = request.data.get('employee')
        date = request.data.get('date')
        
        existing_attendance = Attendance.objects.filter(
            employee_id=employee_id,
            date=date
        ).first()

        if existing_attendance:
            return Response(
                {"error": "Attendance already registered for this employee on this date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['GET'])
    def by_employee(self, request):
        employee_id = request.query_params.get('employee_id')
        if employee_id:
            attendances = Attendance.objects.filter(employee_id=employee_id)
            serializer = self.get_serializer(attendances, many=True)
            return Response(serializer.data)
        return Response({"error": "employee_id is required"}, status=status.HTTP_400_BAD_REQUEST)