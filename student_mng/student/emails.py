from django.core.mail import send_mail
from django.conf import settings

def send_welcome_email(user_email, username):
    subject = "Welcome to our app"
    message = f"Hi {username} \n\nThank you for registering at our site!\n\nBest Regards,\nTeam"
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


def send_add_student_email(user_email, username, password):
    subject = "Welcome to our app"
    message = f" Hi {username} \n\n You were added to our family! \n You can login now with this {password}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


def send_add_course_email(user_email, username, user_course):
    subject = "New course assigned"
    message = f"Hi {username},\n\nYou have been assigned a new course: {user_course}.\n\nAll the best!\nTeam"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
