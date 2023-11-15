# forms.py

from django import forms

class URLCheckForm(forms.Form):
    urls_file = forms.FileField(required=False, label='Upload Excel file with URLs')
    urls_text = forms.CharField(widget=forms.Textarea, required=False, label='Or paste URLs here (one per line)')
