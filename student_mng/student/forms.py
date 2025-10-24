from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Course, StudentProfile, User


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        # this is for save the role as student

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "Student"  # default role for all registered users
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["student_name", "phone", "address", "date_of_birth", "profile_image"]
        # for date picker
        widgets = {
            "student_enrollment_date": forms.DateInput(attrs={"type": "date"}),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "max": date.today().strftime("%Y-%m-%d"),  # Prevent future dates
                }
            ),
        }


class AdminStudentProfileForm(forms.ModelForm):
    student_course = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Assign Courses",
    )  # for assign the multiple courses

    class Meta:
        model = StudentProfile
        fields = [
            "student_name",
            "student_rollno",
            "student_course",
            "student_enrollment_date",
            "phone",
            "address",
            "date_of_birth",
            "age",
            "profile_image",
        ]
        widgets = {
            "student_enrollment_date": forms.DateInput(attrs={"type": "date"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "max": date.today().strftime("%Y-%m-%d")}
            ),
        }


class AdminStudentEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["course_name", "course_description"]
        widgets = {
            "course_name": forms.TextInput(attrs={"class": "form-control"}),
            "course_description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
        }
