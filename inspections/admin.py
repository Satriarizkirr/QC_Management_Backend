from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from .models import Inspection, DefectDetail, InspectionInput, MasterData
import openpyxl
from datetime import datetime
from django.utils import timezone
from django_admin_listfilter_dropdown.filters import DropdownFilter, ChoiceDropdownFilter
from rangefilter.filters import DateRangeFilter

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel File")

class InspectionForm(forms.ModelForm):
    time_range = forms.ChoiceField(choices=[], required=False)
    line = forms.ChoiceField(choices=[], required=False)
    qa_name = forms.ChoiceField(choices=[], required=False)
    qa_id = forms.ChoiceField(choices=[], required=False)
    brand = forms.ChoiceField(choices=[], required=False)
    model = forms.ChoiceField(choices=[], required=False)
    size = forms.ChoiceField(choices=[], required=False)
    colour = forms.ChoiceField(choices=[], required=False)
    item_name = forms.ChoiceField(choices=[], required=False)

    class Meta:
        model = Inspection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fetch choices dynamically from MasterData
        categories = {
            'time_range': 'TIME', 'line': 'LINE', 'qa_name': 'QA_NAME',
            'qa_id': 'QA_ID', 'brand': 'BRAND', 'model': 'MODEL',
            'size': 'SIZE', 'colour': 'COLOUR', 'item_name': 'ITEM',
        }
        try:
            master_qs = MasterData.objects.all()
            grouped = {cat: [] for cat in categories.values()}
            for md in master_qs:
                if md.category in grouped:
                    grouped[md.category].append((md.value, md.value))
            
            for field, cat in categories.items():
                choices = [('', '---------')] + sorted(grouped[cat])
                if field in self.fields:
                    self.fields[field].choices = choices
        except Exception:
            # Fallback if DB is not ready during migrations
            pass

@admin.register(MasterData)
class MasterDataAdmin(admin.ModelAdmin):
    list_display = ('category', 'value')
    list_filter = ('category',)
    search_fields = ('value',)

class DefectDetailInline(admin.TabularInline):
    model = DefectDetail
    extra = 1

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    form = InspectionForm
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    list_display = (
        'date', 'time_range', 'qa_name', 'qa_id', 'shift', 
        'line', 'brand', 'model', 'size', 'colour', 
        'po_no', 'item_name', 'production_output', 'qty_check', 'get_defects'
    )
    
    fieldsets = (
        (None, {
            'classes': ('horizontal-fields',),
            'fields': (
                ('date', 'time_range', 'shift', 'line', 'qa_name', 'qa_id'),
                ('brand', 'model', 'size', 'colour', 'po_no', 'item_name'),
                ('production_output', 'qty_check'),
            )
        }),
    )
    list_filter = (
        ('date', DateRangeFilter),
        ('shift', ChoiceDropdownFilter),
        ('brand', DropdownFilter),
        ('qa_name', DropdownFilter),
    )
    search_fields = ('item_name', 'po_no', 'qa_name')
    inlines = [DefectDetailInline]
    
    change_list_template = "admin/inspections_changelist.html"

    def has_add_permission(self, request):
        """Remove Add button from the main table so users use the specific Input menu."""
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel), name="inspections_inspection_import_excel")
        ]
        return custom_urls + urls

    def get_defects(self, obj):
        defects = obj.defects.all()
        if not defects:
            return "-"
        return ", ".join([f"{d.defect_type} ({d.qty})" for d in defects])
    get_defects.short_description = "Defects"

    def import_excel(self, request):
        if request.method == "POST":
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES["excel_file"]
                try:
                    wb = openpyxl.load_workbook(excel_file, data_only=True)
                    ws = wb.active
                    
                    headers = [cell.value for cell in ws[1]]
                    success_count = 0
                    
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if not any(row): continue
                        
                        row_dict = dict(zip(headers, row))
                        
                        date_val = row_dict.get("DATE")
                        if isinstance(date_val, datetime):
                            date_str = date_val.date()
                        else:
                            date_str = str(date_val).split(" ")[0] if date_val else datetime.now().date()
                        
                        inspection, created = Inspection.objects.get_or_create(
                            date=date_str,
                            time_range=str(row_dict.get("Time") or "08.00-09.00"),
                            qa_name=str(row_dict.get("QA name") or "Unknown"),
                            qa_id=str(row_dict.get("QA ID") or "Unknown"),
                            shift=str(row_dict.get("Shift") or "1"),
                            line=str(row_dict.get("Line") or "Line 1"),
                            brand=str(row_dict.get("Brand") or "Unknown"),
                            model=str(row_dict.get("Model") or "Unknown"),
                            size=str(row_dict.get("Size") or "Unknown"),
                            colour=str(row_dict.get("Colour") or "Unknown"),
                            po_no=str(row_dict.get("Po.No.") or "Unknown"),
                            item_name=str(row_dict.get("Item Name") or "Unknown"),
                            defaults={
                                'production_output': int(row_dict.get("Production Output") or 0),
                                'qty_check': int(row_dict.get("Qty Check") or 0)
                            }
                        )
                        
                        reject_type = row_dict.get("Reject Types")
                        if reject_type:
                            qty_reject = int(row_dict.get("Qty Reject") or 1)
                            repair_method = str(row_dict.get("How to Repair") or "None")
                            
                            DefectDetail.objects.create(
                                inspection=inspection,
                                defect_type=str(reject_type),
                                repair_method=repair_method,
                                qty=qty_reject
                            )
                        
                        success_count += 1
                        
                    self.message_user(request, f"Successfully imported {success_count} rows from Excel.")
                    return redirect("..")
                except Exception as e:
                    self.message_user(request, f"Error processing file: {str(e)}", level=messages.ERROR)
                    return redirect("..")
        else:
            form = ExcelImportForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Import Inspections from Excel',
        }
        return render(request, "admin/excel_import.html", context)

@admin.register(DefectDetail)
class DefectDetailAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'defect_type', 'qty', 'repair_method')
    list_filter = ('defect_type',)
    search_fields = ('defect_type', 'repair_method')


@admin.register(InspectionInput)
class InspectionInputAdmin(admin.ModelAdmin):
    form = InspectionForm
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    """
    Specific menu for INPUT data.
    We keep ADD permission active here.
    """
    list_display = ('item_name', 'date', 'qa_name', 'shift')
    inlines = [DefectDetailInline]
    fieldsets = InspectionAdmin.fieldsets
    change_form_template = "admin/inspections_input_change_form.html"
    
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        today = timezone.now().date()
        # Get up to 15 most recent inspections added today
        recent_inputs = Inspection.objects.filter(created_at__date=today).order_by('-created_at')[:15]
        # Prefetch related defects so it's efficient to display them in the template
        recent_inputs = recent_inputs.prefetch_related('defects')
        context['recent_inputs'] = recent_inputs
        return super().render_change_form(request, context, add, change, form_url, obj)
    
    def has_module_permission(self, request):
        return True

    def changelist_view(self, request, extra_context=None):
        """
        When clicked, immediately redirect to the ADD page so admins don't get confused.
        """
        return redirect('admin:inspections_inspectioninput_add')

