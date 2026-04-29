from django.db import models

class Inspection(models.Model):
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

    def __str__(self):
        return f"{self.item_name} - {self.date} {self.time_range}"


class DefectDetail(models.Model):
    inspection = models.ForeignKey(Inspection, related_name='defects', on_delete=models.CASCADE)
    defect_type = models.CharField(max_length=100)
    repair_method = models.CharField(max_length=100, blank=True, null=True)
    qty = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.defect_type} ({self.qty})"
