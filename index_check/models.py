from django.db import models

class URLCheck(models.Model):
    url = models.URLField()
    is_indexed = models.BooleanField()
    checked_at = models.DateTimeField(auto_now_add=True)

class UrlIndexStatus(models.Model):
    url = models.URLField(max_length=1024)
    is_indexed = models.CharField(max_length=15, null=True, blank=True, choices=(('Indexed', 'Indexed'), ('Not Indexed', 'Not Indexed')))

    def __str__(self):
        return f"{self.url} - {self.is_indexed}"
