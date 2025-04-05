from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TemplateItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('income', '収入'),
        ('expense', '支出'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.price}円)"
    
class Record(models.Model):
    ITEM_TYPE_CHOICES = [
        ('income', '収入'),
        ('expense', '支出'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField('内容', max_length=100)
    amount = models.PositiveIntegerField('金額')
    item_type = models.CharField('種別', max_length=10, choices=ITEM_TYPE_CHOICES)
    date = models.DateField('日付', default=timezone.now)
    receipt_image = models.ImageField('レシート画像', upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.amount}円 ({self.item_type})"