from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **kawrgs):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **kawrgs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kawrgs):
        if not kawrgs:
            kawrgs = {}
        kawrgs.setdefault("is_staff", True)
        kawrgs.setdefault("verified", True)

        if kawrgs.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))

        return self.create_user(email, password, **kawrgs)


class Student(AbstractBaseUser):
    # TODO to create id using uuidv7
    # TODO to create code for student
    # EmailField by default contains validators.validate_email()
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(
        validators=[MinLengthValidator(3), MaxLengthValidator(255)],
    )
    verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blocked = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_admin(self):
        "Is the user admin?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def num_of_reviews(self):
        return self.user_reviews.count()

    def __str__(self):
        return str(self.email)
