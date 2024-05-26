from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UsersManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Users(AbstractBaseUser):
    name = models.CharField(max_length=50, blank=True, null=True)
    surname = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True, null=False)
    gender = models.CharField(max_length=6, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    REQUIRED_FIELDS = ['name', 'surname', 'gender', 'birth_date']

    objects = UsersManager()

    USERNAME_FIELD = 'email'

    class Meta:
        db_table = 'users'
        managed = True

    def __str__(self):
        return f'{self.name} {self.surname}'

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True


class Organizations(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo_photo_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'organizations'
        managed = True

    def __str__(self):
        return self.name


class Events(models.Model):
    organization = models.ForeignKey(Organizations, models.CASCADE, db_column='OrganizationID', blank=True, null=True)
    user = models.ForeignKey(Users, models.CASCADE, db_column='UserID', blank=True, null=True)
    event_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    banner = models.CharField(max_length=255, blank=True, null=True)
    max_participants = models.IntegerField(default=110)
    class Meta:
        db_table = 'events'
        managed = True

    def __str__(self):
        return self.event_name


class OrganizationMembers(models.Model):
    organization = models.ForeignKey(Organizations, models.CASCADE, db_column='OrganizationID', blank=True, null=True)
    user = models.ForeignKey(Users, models.CASCADE, db_column='UserID', blank=True, null=True)
    access_level = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        db_table = 'organizationmembers'
        managed = True

    def __str__(self):
        return f'{self.user} - {self.organization} ({self.access_level})'


class Roles(models.Model):
    event = models.ForeignKey(Events, models.CASCADE, db_column='EventID', blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    allowed_number_of_users = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'roles'
        managed = True

    def __str__(self):
        return self.role


class Participants(models.Model):
    event = models.ForeignKey(Events, models.CASCADE, db_column='EventID', blank=True, null=True)
    user = models.ForeignKey(Users, models.CASCADE, db_column='UserID', blank=True, null=True)
    role = models.ForeignKey(Roles, models.CASCADE, db_column='RoleID', blank=True, null=True)
    registration_time = models.DateTimeField(default=timezone.now)  # Add this field

    class Meta:
        db_table = 'participants'
        managed = True

    def __str__(self):
        return f'{self.user} - {self.event} ({self.role})'


class AdditionalModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'additional_model'
