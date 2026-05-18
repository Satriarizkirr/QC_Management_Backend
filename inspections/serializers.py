from rest_framework import serializers
from .models import Inspection, DefectDetail, AssemblingInspection, AssemblingDefectDetail

class DefectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectDetail
        fields = ['id', 'defect_type', 'repair_method', 'qty']

class InspectionSerializer(serializers.ModelSerializer):
    defects = DefectDetailSerializer(many=True, required=False)

    class Meta:
        model = Inspection
        fields = [
            'id', 'date', 'time_range', 'qa_name', 'qa_id', 'shift', 
            'line', 'brand', 'model', 'size', 'colour', 'po_no', 
            'item_name', 'production_output', 'qty_check', 'defects', 
            'created_at'
        ]

    def create(self, validated_data):
        defects_data = validated_data.pop('defects', [])
        inspection = Inspection.objects.create(**validated_data)
        for defect_data in defects_data:
            DefectDetail.objects.create(inspection=inspection, **defect_data)
        return inspection

class AssemblingDefectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssemblingDefectDetail
        fields = ['id', 'defect_type', 'qty']

class AssemblingInspectionSerializer(serializers.ModelSerializer):
    defects = AssemblingDefectDetailSerializer(many=True, required=False)

    class Meta:
        model = AssemblingInspection
        fields = [
            'id', 'date', 'line', 'shift', 'qa_name', 'qa_id', 'po_no',
            'brand', 'model', 'size', 'colour',
            'qty_check_hours', 'defect_quantity', 'defect_rate', 'defects',
            'created_at'
        ]

    def create(self, validated_data):
        defects_data = validated_data.pop('defects', [])
        inspection = AssemblingInspection.objects.create(**validated_data)
        for defect_data in defects_data:
            AssemblingDefectDetail.objects.create(inspection=inspection, **defect_data)
        return inspection
