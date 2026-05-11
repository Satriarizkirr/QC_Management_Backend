from django.db import models

class Inspection(models.Model):
    objects = models.Manager()
    SHIFT_CHOICES = [
        ('1', 'Shift 1'),
        ('2', 'Shift 2'),
        ('3', 'Shift 3'),
    ]

    date = models.DateField()
    time_range = models.CharField(max_length=50) # e.g. "06.30-07.30"
    qa_name = models.CharField(max_length=100)
    qa_id = models.CharField(max_length=50)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    line = models.CharField(max_length=50)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    colour = models.CharField(max_length=50)
    po_no = models.CharField(max_length=100)
    item_name = models.CharField(max_length=150)
    
    production_output = models.IntegerField(default=0)
    qty_check = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sewing inspection"
        verbose_name_plural = "Sewing inspections"

    def __str__(self):
        return f"{self.item_name} - {self.date} {self.time_range}"


class DefectDetail(models.Model):
    objects = models.Manager()
    inspection = models.ForeignKey(Inspection, related_name='defects', on_delete=models.CASCADE)
    defect_type = models.CharField(max_length=100)
    repair_method = models.CharField(max_length=100, blank=True, null=True)
    qty = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Sewing defect detail"
        verbose_name_plural = "Sewing defect details"

    def __str__(self):
        return f"{self.defect_type} ({self.qty})"


class InspectionInput(Inspection):
    class Meta:
        proxy = True
        verbose_name = "Input Sewing"
        verbose_name_plural = "Input Sewing"

class MasterData(models.Model):
    objects = models.Manager()
    CATEGORY_CHOICES = [
        ('TIME', 'Time Range'),
        ('LINE', 'Line'),
        ('QA_NAME', 'QA Name'),
        ('QA_ID', 'QA ID'),
        ('BRAND', 'Brand'),
        ('MODEL', 'Model'),
        ('SIZE', 'Size'),
        ('COLOUR', 'Colour'),
        ('ITEM', 'Item Name'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    value = models.CharField(max_length=150)

    class Meta:
        unique_together = ('category', 'value')
        verbose_name = "Master Data Sewing"
        verbose_name_plural = "Master Data Sewing"

    def __str__(self):
        return f"{self.get_category_display()}: {self.value}"


class AssemblingInspection(models.Model):
    objects = models.Manager()
    SHIFT_CHOICES = [
        ('1', 'Shift 1'),
        ('2', 'Shift 2'),
        ('3', 'Shift 3'),
    ]

    date = models.DateField()
    line = models.CharField(max_length=50)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    qa_name = models.CharField(max_length=100)
    qa_id = models.CharField(max_length=50)
    po_no = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    colour = models.CharField(max_length=50)
    
    inspection_quantity = models.IntegerField(default=0)
    qty_check_hours = models.IntegerField(default=0)
    defect_quantity = models.IntegerField(default=0)
    defect_rate = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Assembling inspection"
        verbose_name_plural = "Assembling inspections"

    def __str__(self):
        return f"Assembling - {self.po_no} - {self.date}"


class AssemblingDefectDetail(models.Model):
    objects = models.Manager()
    inspection = models.ForeignKey(AssemblingInspection, related_name='defects', on_delete=models.CASCADE)
    defect_type = models.CharField(max_length=100)
    qty = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Assembling defect detail"
        verbose_name_plural = "Assembling defect details"

    def __str__(self):
        return f"{self.defect_type} ({self.qty})"


class AssemblingInspectionInput(AssemblingInspection):
    class Meta:
        proxy = True
        verbose_name = "Input Assembling"
        verbose_name_plural = "Input Assembling"


class AssemblingMasterData(models.Model):
    objects = models.Manager()
    CATEGORY_CHOICES = [
        ('LINE', 'Line'),
        ('QA_NAME', 'QA Name'),
        ('QA_ID', 'QA ID'),
        ('BRAND', 'Brand'),
        ('MODEL', 'Model'),
        ('SIZE', 'Size'),
        ('COLOUR', 'Colour'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    value = models.CharField(max_length=150)

    class Meta:
        unique_together = ('category', 'value')
        verbose_name = "Master Data Assembling"
        verbose_name_plural = "Master Data Assembling"

    def __str__(self):
        return f"{self.get_category_display()}: {self.value}"

