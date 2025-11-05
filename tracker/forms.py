from django import forms
from .models import ActivityLog

class ActivityLogForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = ['emails_sent', 'drive_storage_gb', 'github_commits']
        widgets = {
            'emails_sent': forms.NumberInput(attrs={
                'class': 'w-full bg-slate-700 text-white border border-slate-600 rounded-lg py-2 px-10 focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
            'drive_storage_gb': forms.NumberInput(attrs={
                'class': 'w-full bg-slate-700 text-white border border-slate-600 rounded-lg py-2 px-10 focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
            'github_commits': forms.NumberInput(attrs={
                'class': 'w-full bg-slate-700 text-white border border-slate-600 rounded-lg py-2 px-10 focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
        }
