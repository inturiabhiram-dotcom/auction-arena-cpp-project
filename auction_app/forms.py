from django import forms
from .models import UserModel


class signup(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserModel
        fields = ["username", "email", "firstname", "lastname", "phone", "password"] # Use correct field names
    
    def __init__(self, *args, **kwargs):
        super(signup, self).__init__(*args, **kwargs)
        self.fields["username"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

