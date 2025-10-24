from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
class User(AbstractUser):
    ROLE_CHOICES=(
        ('Admin','Admin'),#first admin for storing name in db,and second for what to show the user
        ('Student','Student')
    )
    role=models.CharField(max_length=10,choices=ROLE_CHOICES,default='Student')
    def __str__(self):
        return f"{self.username},{self.role}"
    #this is for set the role of superuser as "Admin",so when super user login role become admin
@receiver(post_save, sender=User)
def set_admin_role(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        instance.role = 'Admin'
        instance.save()    
class Course(models.Model):
    course_name=models.CharField(max_length=50)
    course_description=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)# automatically set when created
    updated_at=models.DateTimeField(auto_now=True) # automatically updated when saved
    def __str__(self):
        return self.course_name


class StudentProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    student_name = models.CharField(max_length=50, null=True, blank=True)
    student_rollno = models.IntegerField(null=True, blank=True, unique=True)
    student_course = models.ManyToManyField('Course', blank=True)
    student_enrollment_date = models.DateField(null=True, blank=True)

    # Editable by student
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True) 
    age = models.IntegerField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images', null=True, blank=True)
    
    def __str__(self):
        return self.student_name or self.user.username