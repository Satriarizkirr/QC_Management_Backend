from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Inspection, DefectDetail, AssemblingInspection, AssemblingDefectDetail
from .serializers import InspectionSerializer, DefectDetailSerializer, AssemblingInspectionSerializer, AssemblingDefectDetailSerializer

class DashboardStatsView(APIView):
    def get(self, request):
        process_type = request.query_params.get('process', 'sewing').lower()
        
        brand = request.query_params.get('brand')
        line = request.query_params.get('line')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        defect_type = request.query_params.get('defect_type')

        if process_type == 'assembling':
            return self.get_assembling_stats(request, brand, line, start_date, end_date, defect_type)
        else:
            return self.get_sewing_stats(request, brand, line, start_date, end_date, defect_type)

    def get_assembling_stats(self, request, brand, line, start_date, end_date, defect_type):
        from .models import AssemblingInspection, AssemblingDefectDetail
        inspections = AssemblingInspection.objects.all()

        if brand: inspections = inspections.filter(brand=brand)
        if line: inspections = inspections.filter(line=line)
        if start_date: inspections = inspections.filter(date__gte=start_date)
        if end_date: inspections = inspections.filter(date__lte=end_date)

        totals = inspections.aggregate(
            total_production=Sum('qty_check_hours'),
            total_checked=Sum('qty_check_hours')
        )
        total_production = totals['total_production'] or 0
        total_checked = totals['total_checked'] or 0

        defects = AssemblingDefectDetail.objects.all()
        if brand: defects = defects.filter(inspection__brand=brand)
        if line: defects = defects.filter(inspection__line=line)
        if start_date: defects = defects.filter(inspection__date__gte=start_date)
        if end_date: defects = defects.filter(inspection__date__lte=end_date)
        
        if defect_type:
            defects = defects.filter(defect_type=defect_type)
            
        top_defects_flag = request.query_params.get('top_defects') == 'true'
        if top_defects_flag:
            top_5 = list(defects.values('defect_type').annotate(count=Sum('qty')).order_by('-count')[:5].values_list('defect_type', flat=True))
            defects = defects.filter(defect_type__in=top_5)

        total_defects = defects.aggregate(total=Sum('qty'))['total'] or 0
        defect_rate = (total_defects / total_checked * 100) if total_checked > 0 else 0

        # Pareto Data
        defect_types = defects.values('defect_type').annotate(count=Sum('qty')).order_by('-count')
        pareto_data = []
        cumulative = 0
        for dt in defect_types:
            cumulative += dt['count']
            pareto_data.append({
                'name': dt['defect_type'],
                'value': dt['count'],
                'cumulative_percent': round((cumulative / total_defects * 100), 2) if total_defects > 0 else 0
            })

        # Trend Data
        trend_headers = inspections.values('date').annotate(
            production=Sum('qty_check_hours'),
            checked=Sum('qty_check_hours')
        ).order_by('date')
        
        trend_defects = defects.values('inspection__date').annotate(
            defects_count=Sum('qty')
        ).order_by('inspection__date')
        
        defects_map = {str(d['inspection__date']): d['defects_count'] or 0 for d in trend_defects}
        
        trend_data = []
        weekly_dict = {}
        monthly_dict = {}

        for t in trend_headers:
            d = t['date']
            if not d: continue
            
            d_str = str(d)
            defects_count = defects_map.get(d_str, 0)
            
            trend_data.append({
                'date': d_str,
                'defects': defects_count,
                'checked': t['checked'] or 0,
            })
            
            week_str = d.strftime('%Y-W%V')
            if week_str not in weekly_dict:
                weekly_dict[week_str] = {'checked': 0, 'defects': 0}
            weekly_dict[week_str]['checked'] += (t['checked'] or 0)
            weekly_dict[week_str]['defects'] += defects_count
            
            month_str = d.strftime('%Y-%m')
            if month_str not in monthly_dict:
                monthly_dict[month_str] = {'checked': 0, 'defects': 0}
            monthly_dict[month_str]['checked'] += (t['checked'] or 0)
            monthly_dict[month_str]['defects'] += defects_count

        trend_weekly_data = []
        for k, v in sorted(weekly_dict.items()):
            rate = (v['defects'] / v['checked'] * 100) if v['checked'] else 0
            trend_weekly_data.append({
                'name': k,
                'rate': round(rate, 2),
                'defects': v['defects']
            })

        trend_monthly_data = []
        for k, v in sorted(monthly_dict.items()):
            rate = (v['defects'] / v['checked'] * 100) if v['checked'] else 0
            trend_monthly_data.append({
                'name': k,
                'rate': round(rate, 2),
                'defects': v['defects']
            })

        brands = AssemblingInspection.objects.values_list('brand', flat=True).distinct()
        lines = AssemblingInspection.objects.values_list('line', flat=True).distinct()
        all_defect_types = AssemblingDefectDetail.objects.values_list('defect_type', flat=True).distinct()

        from datetime import datetime, timedelta
        if end_date:
            try:
                reference_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                reference_date = datetime.now().date()
        else:
            reference_date = datetime.now().date()
            
        week_ago = reference_date - timedelta(days=7)
        month_ago = reference_date - timedelta(days=30)
        
        base_inspections = AssemblingInspection.objects.all()
        if brand: base_inspections = base_inspections.filter(brand=brand)
        if line: base_inspections = base_inspections.filter(line=line)
        if start_date: base_inspections = base_inspections.filter(date__gte=start_date)
        if end_date: base_inspections = base_inspections.filter(date__lte=end_date)
        
        weekly_inspections = base_inspections.filter(date__gte=week_ago)
        monthly_inspections = base_inspections.filter(date__gte=month_ago)

        w_header = weekly_inspections.aggregate(prod=Sum('qty_check_hours'), chk=Sum('qty_check_hours'))
        w_defects = defects.filter(inspection__date__gte=week_ago).aggregate(total_def=Sum('qty'))
        
        w_chk = w_header['chk'] or 0
        w_def = w_defects['total_def'] or 0
        w_rate = (w_def / w_chk * 100) if w_chk > 0 else 0

        m_header = monthly_inspections.aggregate(prod=Sum('qty_check_hours'), chk=Sum('qty_check_hours'))
        m_defects = defects.filter(inspection__date__gte=month_ago).aggregate(total_def=Sum('qty'))
        
        m_chk = m_header['chk'] or 0
        m_def = m_defects['total_def'] or 0
        m_rate = (m_def / m_chk * 100) if m_chk > 0 else 0

        return Response({
            'kpis': {
                'total_production': total_production,
                'total_checked': total_checked,
                'total_defects': total_defects,
                'defect_rate': round(defect_rate, 2),
                'weekly_rate': round(w_rate, 2),
                'monthly_rate': round(m_rate, 2),
                'weekly_checked': w_chk,
                'monthly_checked': m_chk
            },
            'pareto': pareto_data,
            'trend': trend_data,
            'trend_weekly': trend_weekly_data,
            'trend_monthly': trend_monthly_data,
            'filters': {
                'brands': sorted([b for b in brands if b]),
                'lines': sorted([l for l in lines if l]),
                'defect_types': sorted([d for d in all_defect_types if d])
            }
        })

    def get_sewing_stats(self, request, brand, line, start_date, end_date, defect_type):
        inspections = Inspection.objects.all()

        if brand: inspections = inspections.filter(brand=brand)
        if line: inspections = inspections.filter(line=line)
        if start_date: inspections = inspections.filter(date__gte=start_date)
        if end_date: inspections = inspections.filter(date__lte=end_date)

        totals = inspections.aggregate(
            total_production=Sum('production_output'),
            total_checked=Sum('qty_check')
        )
        total_production = totals['total_production'] or 0
        total_checked = totals['total_checked'] or 0

        defects = DefectDetail.objects.all()
        if brand: defects = defects.filter(inspection__brand=brand)
        if line: defects = defects.filter(inspection__line=line)
        if start_date: defects = defects.filter(inspection__date__gte=start_date)
        if end_date: defects = defects.filter(inspection__date__lte=end_date)
        
        if defect_type:
            defects = defects.filter(defect_type=defect_type)
            
        top_defects_flag = request.query_params.get('top_defects') == 'true'
        if top_defects_flag:
            top_5 = list(defects.values('defect_type').annotate(count=Sum('qty')).order_by('-count')[:5].values_list('defect_type', flat=True))
            defects = defects.filter(defect_type__in=top_5)

        total_defects = defects.aggregate(total=Sum('qty'))['total'] or 0
        defect_rate = (total_defects / total_checked * 100) if total_checked > 0 else 0

        # Pareto Data
        defect_types = defects.values('defect_type').annotate(count=Sum('qty')).order_by('-count')
        pareto_data = []
        cumulative = 0
        for dt in defect_types:
            cumulative += dt['count']
            pareto_data.append({
                'name': dt['defect_type'],
                'value': dt['count'],
                'cumulative_percent': round((cumulative / total_defects * 100), 2) if total_defects > 0 else 0
            })

        # Trend Data
        trend_headers = inspections.values('date').annotate(
            production=Sum('production_output'),
            checked=Sum('qty_check')
        ).order_by('date')
        
        trend_defects = defects.values('inspection__date').annotate(
            defects_count=Sum('qty')
        ).order_by('inspection__date')
        
        defects_map = {str(d['inspection__date']): d['defects_count'] or 0 for d in trend_defects}
        
        trend_data = []
        weekly_dict = {}
        monthly_dict = {}

        for t in trend_headers:
            d = t['date']
            if not d: continue
            
            d_str = str(d)
            defects_count = defects_map.get(d_str, 0)
            
            trend_data.append({
                'date': d_str,
                'defects': defects_count,
                'checked': t['checked'] or 0,
            })
            
            week_str = d.strftime('%Y-W%V')
            if week_str not in weekly_dict:
                weekly_dict[week_str] = {'checked': 0, 'defects': 0}
            weekly_dict[week_str]['checked'] += (t['checked'] or 0)
            weekly_dict[week_str]['defects'] += defects_count
            
            month_str = d.strftime('%Y-%m')
            if month_str not in monthly_dict:
                monthly_dict[month_str] = {'checked': 0, 'defects': 0}
            monthly_dict[month_str]['checked'] += (t['checked'] or 0)
            monthly_dict[month_str]['defects'] += defects_count

        trend_weekly_data = []
        for k, v in sorted(weekly_dict.items()):
            rate = (v['defects'] / v['checked'] * 100) if v['checked'] else 0
            trend_weekly_data.append({
                'name': k,
                'rate': round(rate, 2),
                'defects': v['defects']
            })

        trend_monthly_data = []
        for k, v in sorted(monthly_dict.items()):
            rate = (v['defects'] / v['checked'] * 100) if v['checked'] else 0
            trend_monthly_data.append({
                'name': k,
                'rate': round(rate, 2),
                'defects': v['defects']
            })

        brands = Inspection.objects.values_list('brand', flat=True).distinct()
        lines = Inspection.objects.values_list('line', flat=True).distinct()
        all_defect_types = DefectDetail.objects.values_list('defect_type', flat=True).distinct()

        from datetime import datetime, timedelta
        if end_date:
            try:
                reference_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                reference_date = datetime.now().date()
        else:
            reference_date = datetime.now().date()
            
        week_ago = reference_date - timedelta(days=7)
        month_ago = reference_date - timedelta(days=30)
        
        base_inspections = Inspection.objects.all()
        if brand: base_inspections = base_inspections.filter(brand=brand)
        if line: base_inspections = base_inspections.filter(line=line)
        if start_date: base_inspections = base_inspections.filter(date__gte=start_date)
        if end_date: base_inspections = base_inspections.filter(date__lte=end_date)
        
        weekly_inspections = base_inspections.filter(date__gte=week_ago)
        monthly_inspections = base_inspections.filter(date__gte=month_ago)

        w_header = weekly_inspections.aggregate(prod=Sum('production_output'), chk=Sum('qty_check'))
        w_defects = defects.filter(inspection__date__gte=week_ago).aggregate(total_def=Sum('qty'))
        
        w_chk = w_header['chk'] or 0
        w_def = w_defects['total_def'] or 0
        w_rate = (w_def / w_chk * 100) if w_chk > 0 else 0

        m_header = monthly_inspections.aggregate(prod=Sum('production_output'), chk=Sum('qty_check'))
        m_defects = defects.filter(inspection__date__gte=month_ago).aggregate(total_def=Sum('qty'))
        
        m_chk = m_header['chk'] or 0
        m_def = m_defects['total_def'] or 0
        m_rate = (m_def / m_chk * 100) if m_chk > 0 else 0

        return Response({
            'kpis': {
                'total_production': total_production,
                'total_checked': total_checked,
                'total_defects': total_defects,
                'defect_rate': round(defect_rate, 2),
                'weekly_rate': round(w_rate, 2),
                'monthly_rate': round(m_rate, 2),
                'weekly_checked': w_chk,
                'monthly_checked': m_chk
            },
            'pareto': pareto_data,
            'trend': trend_data,
            'trend_weekly': trend_weekly_data,
            'trend_monthly': trend_monthly_data,
            'filters': {
                'brands': sorted([b for b in brands if b]),
                'lines': sorted([l for l in lines if l]),
                'defect_types': sorted([d for d in all_defect_types if d])
            }
        })

class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all().order_by('-created_at')
    serializer_class = InspectionSerializer

class DefectDetailViewSet(viewsets.ModelViewSet):
    queryset = DefectDetail.objects.all()
    serializer_class = DefectDetailSerializer

class AssemblingInspectionViewSet(viewsets.ModelViewSet):
    queryset = AssemblingInspection.objects.all().order_by('-created_at')
    serializer_class = AssemblingInspectionSerializer

class AssemblingDefectDetailViewSet(viewsets.ModelViewSet):
    queryset = AssemblingDefectDetail.objects.all()
    serializer_class = AssemblingDefectDetailSerializer
