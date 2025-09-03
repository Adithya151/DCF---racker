from django import forms
from .models import ActivityLog

class ActivityLogForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = ['emails_sent', 'drive_storage_gb', 'github_commits']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'emails_sent': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border border-slate-600 bg-white text-slate-900 px-10 py-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Enter number of emails',
            }),
            'drive_storage_gb': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border border-slate-600 bg-white text-slate-900 px-10 py-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Enter storage in GB',
            }),
            'github_commits': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border border-slate-600 bg-white text-slate-900 px-10 py-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Enter commits count',
            }),
        }
        
        

