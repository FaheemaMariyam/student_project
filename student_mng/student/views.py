from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegisterForm
from .forms import StudentProfileForm
from .models import StudentProfile
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from datetime import date
from .forms import AdminStudentProfileForm

from .forms import AdminStudentEditForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from student_mng.settings import EMAIL_HOST_USER
from .emails import send_welcome_email, send_add_student_email, send_add_course_email
from .forms import CourseForm
from .models import Course


def home(request):
    return render(request, "home.html")


def about_us(request):
    return render(request, "about.html")


def register_user(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = user.username
            email = user.email
            # welcome email

            send_welcome_email(email, username)
            messages.success(request, f"Registation successfull,you can login now")
            return redirect("login")

        else:
            print(form.errors)  # 🔍 See errors in terminal
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")


@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def dashboard(request):
    students = StudentProfile.objects.filter(user__role="Student")
    user = request.user
    if user.is_superuser or user.role == "Admin":
        return render(
            request, "admin_dashboard.html", {"user": user, "students": students}
        )
    elif user.role == "Student":
        return render(request, "student_dashboard.html", {"user": user})
    else:
        return HttpResponse("Role not specified")


@login_required
def student_profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    return render(request, "student_profile_view.html", {"profile": profile})


@login_required
def student_profile_edit(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            student = form.save(commit=False)
            # calculate age from dob
            if student.date_of_birth:
                today = date.today()
                age = today.year - student.date_of_birth.year
                if (today.month, today.day) < (
                    student.date_of_birth.month,
                    student.date_of_birth.day,
                ):
                    age -= 1
                student.age = age
            student.save()
            return redirect("dashboard")
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, "student_profile_edit.html", {"form": form})


@login_required
def student_courses_view(request):
    profile = StudentProfile.objects.get(user=request.user)
    courses = profile.student_course.all()

    # Retrieve completed courses from session (if any)
    completed_ids = request.session.get("completed_courses", [])

    if request.method == "POST":
        completed_ids = request.POST.getlist("completed")
        request.session["completed_courses"] = completed_ids  # Save to session

    # Add a flag to each course for template rendering
    course_data = []
    for course in courses:
        course_data.append({
            "id": course.id,
            "name": course.course_name,
            "description": course.course_description,
            "completed": str(course.id) in completed_ids,
        })

    return render(request, "student_courses.html", {"courses": course_data})


@staff_member_required
def students_list(request):

    # students=StudentProfile.objects.filter(user__role='Student',
    #                                        student_name__istartswith='r'
    #                                        )
    students = StudentProfile.objects.filter(user__role="Student")
    # get the data from url query parameter'q'
    query = request.GET.get("q")

    # if user type something
    if query:
        students = students.filter(
            student_name__icontains=query
        )  # icontains=for casesensitivity
    # pagination
    paginator = Paginator(students, 5)
    # get page number from query
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "students_list.html",
        {"students": students, "query": query, "page_obj": page_obj},
    )  # query for keep the query in search box


@staff_member_required
def add_students(request):
    if request.method == "POST":
        user_form = UserRegisterForm(
            request.POST
        )  # this used bcz it is not null column,so admin add the username,and password
        profile_form = AdminStudentProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            # for Create the user first
            user = user_form.save(commit=False)
            username = user.username
            raw_password = user_form.cleaned_data["password1"]
            email = user.email
            user.role = "Student"
            user.save()
            # Create student profile and link the user
            student = profile_form.save(commit=False)
            student.user = user
            student.save()
            if student.date_of_birth:
                today = date.today()
                age = today.year - student.date_of_birth.year
                if (today.month, today.day) < (
                    student.date_of_birth.month,
                    student.date_of_birth.day,
                ):
                    age -= 1
                student.age = age
            student.save()
            send_add_student_email(email, username, raw_password)
            messages.success(request, f"{student.student_name} added successfully ")
            return redirect("dashboard")
    else:
        user_form = UserRegisterForm()
        profile_form = AdminStudentProfileForm()
    return render(
        request,
        "add_students.html",
        {"user_form": user_form, "profile_form": profile_form},
    )



@staff_member_required
def edit_students(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)

    # 🔹 Store old courses before updating
    old_courses = set(student.student_course.all())

    if request.method == "POST":
        user_form = AdminStudentEditForm(request.POST, instance=student.user)
        profile_form = AdminStudentProfileForm(
            request.POST, request.FILES, instance=student
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()

            # Save student instance (but not m2m yet)
            student = profile_form.save(commit=False)

            # 🔹 Recalculate age
            if student.date_of_birth:
                today = date.today()
                age = today.year - student.date_of_birth.year
                if (today.month, today.day) < (
                    student.date_of_birth.month,
                    student.date_of_birth.day,
                ):
                    age -= 1
                student.age = age
            else:
                student.age = None

            student.save()

            # Save ManyToMany relationships
            profile_form.save_m2m()

            # 🔹 Get new courses after saving
            new_courses = set(student.student_course.all()) - old_courses

            # 🔹 Send notification only for newly assigned courses
            if new_courses:
                for course in new_courses:
                    send_add_course_email(
                        student.user.email,
                        student.user.username,
                        course.course_name,
                    )

            messages.success(
                request,
                f"{student.student_name or student.user.username} updated successfully."
                + (f" {len(new_courses)} new course(s) assigned." if new_courses else "")
            )
            return redirect("dashboard")

    else:
        user_form = AdminStudentEditForm(instance=student.user)
        profile_form = AdminStudentProfileForm(instance=student)

    return render(
        request,
        "edit_students.html",
        {"user_form": user_form, "profile_form": profile_form},
    )

@staff_member_required
def delete_students(request, pk):
    students_qset = StudentProfile.objects.filter(pk=pk)
    if not students_qset.exists():
        messages.error(request, f"student not found")
        return redirect("dashboard")
    student = students_qset.first()
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, f"{student.student_name} has been deleted successfully")
    return redirect("dashboard")


@staff_member_required
def add_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, "Course added successfully")
            return redirect("dashboard")
    else:
        form = CourseForm()
    return render(request, "add_course.html", {"form": form})


@staff_member_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "course_list.html", {"courses": courses})


@staff_member_required
def edit_course(request, pk):
    course_qset = Course.objects.filter(pk=pk)
    if not course_qset.exists():
        messages.error(request, f"course doesnt exist")
        return redirect("dashboard")
    course = course_qset.first()
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course updated successfully")
            return redirect("dashboard")
    else:
        form = CourseForm(instance=course)
    return render(request, "edit_course.html", {"form": form})


@staff_member_required
def delete_course(request, pk):
    course_qset = Course.objects.filter(pk=pk)
    if not course_qset.exists():
        messages.error(request, f" Course does not exist ")
        return redirect("dashboard")
    course = course_qset.first()

    course_name = course.course_name  # store before delete

    course.delete()
    messages.success(request, f" {course_name} has been deleted successfully ")
    return redirect("dashboard")
