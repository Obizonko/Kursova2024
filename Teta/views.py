from django.shortcuts import render, get_object_or_404, redirect
from Teta.models import Users, Organizations, OrganizationMembers, Events, Roles, Participants
from Delta.forms import UserRegistrationForm, UserLoginForm, OrganizationForm, EventForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.db.models import Count, F, Q

# Отримання списку користувачів
def user_list(request):
    users = Users.objects.all()
    return render(request, 'user_list.html', {'Delta': users})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})



@login_required
def create_organization(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            organization = form.save()
            # Add the user as the organization leader
            organization_member = OrganizationMembers.objects.create(
                organization=organization,
                user=request.user,
                access_level='leader'
            )
            return redirect('home')
    else:
        form = OrganizationForm()
    return render(request, 'create_organization.html', {'form': form})


@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            if event.organization in Organizations.objects.filter(organizationmembers__user=request.user):
                event.save()
            # Create default roles 'member' and 'wait'
            Roles.objects.create(event=event, role='member', allowed_number_of_users=event.max_participants)
            Roles.objects.create(event=event, role='wait', allowed_number_of_users=None)
            num_roles = int(request.POST.get('num_roles', 0))
            for i in range(num_roles):
                role_name = request.POST.get(f'role_name_{i}')
                allowed_number = int(request.POST.get(f'allowed_number_{i}', 1))
                email = request.POST.get(f'email_{i}')
                role = Roles.objects.create(
                    event=event,
                    role=role_name,
                    allowed_number_of_users=allowed_number
                )
                if email:
                    user = Users.objects.filter(email=email).first()
                    if user:
                        Participants.objects.create(
                            event=event,
                            user=user,
                            role=role
                        )
            return redirect('home')
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Events, pk=event_id)
    participants = Participants.objects.filter(event=event).select_related('user', 'role')

    if request.method == 'POST':
        selected_role_id = request.POST.get('role')
        selected_role = get_object_or_404(Roles, pk=selected_role_id)

        # Check if the user is already registered for the event
        if Participants.objects.filter(event=event, user=request.user).exists():
            messages.error(request, "You are already registered for this event.")
        else:
            # Check available slots for the selected role
            current_count = Participants.objects.filter(event=event, role=selected_role).count()
            if selected_role.allowed_number_of_users is not None and current_count >= selected_role.allowed_number_of_users:
                messages.error(request, "No available slots for the selected role.")
                return redirect('event_detail', event_id=event_id)

            # Assign the "member" role or "wait" role based on availability
            if selected_role.role == 'member' and current_count < selected_role.allowed_number_of_users:
                Participants.objects.create(event=event, user=request.user, role=selected_role)
                messages.success(request, "You have been registered as a member.")
            else:
                wait_role = Roles.objects.get(event=event, role='wait')
                Participants.objects.create(event=event, user=request.user, role=wait_role)
                messages.success(request, "No available slots. You have been added to the waitlist.")

        return redirect('event_detail', event_id=event_id)

    # Filter roles based on availability
    available_roles = Roles.objects.filter(event=event).annotate(
        current_count=Count('participants')
    ).filter(
        Q(allowed_number_of_users__isnull=True) | Q(current_count__lt=F('allowed_number_of_users'))
    )

    return render(request, 'event_detail.html', {
        'event': event,
        'participants': participants,
        'roles': available_roles,
    })

@login_required
def home(request):
    events = Events.objects.all()
    organizations = Organizations.objects.all()  # Отримати всі організації
    return render(request, 'home.html', {'events': events, 'organizations': organizations})

@login_required
def organization_detail(request, organization_id):
    organization = get_object_or_404(Organizations, pk=organization_id)
    events = Events.objects.filter(organization=organization)
    return render(request, 'organization_detail.html', {'organization': organization, 'events': events})
@login_required
def logout_view(request):
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            logout(request)
            return redirect('login')
        else:
            return redirect('home')
    return render(request, 'logout_confirmation.html')


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Events, pk=event_id)

    if event.organization in Organizations.objects.filter(organizationmembers__user=request.user):
        return redirect('event_detail', event_id=event_id)

    RoleFormSet = modelformset_factory(Roles, fields=('role', 'allowed_number_of_users'), extra=0, can_delete=True)
    ParticipantFormSet = modelformset_factory(Participants, fields=('role',), extra=0)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        role_formset = RoleFormSet(request.POST, queryset=Roles.objects.filter(event=event))
        participant_formset = ParticipantFormSet(request.POST, queryset=Participants.objects.filter(event=event))

        if form.is_valid() and role_formset.is_valid() and participant_formset.is_valid():
            form.save()
            role_formset.save()
            participant_formset.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
        role_formset = RoleFormSet(queryset=Roles.objects.filter(event=event))
        participant_formset = ParticipantFormSet(queryset=Participants.objects.filter(event=event))

    return render(request, 'edit_event.html', {
        'form': form,
        'role_formset': role_formset,
        'participant_formset': participant_formset,
        'event': event
    })
