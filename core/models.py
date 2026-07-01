from django.db import models

class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name
    
class District(models.Model):
    province = models.ForeignKey(Province,on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
