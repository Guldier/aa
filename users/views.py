from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Profile
from django.core.exceptions import ObjectDoesNotExist

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Welcome! You are now able to login {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
        messages.error(request, 'Upss')
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = Profile(user=request.user)
        profile.save()

    context  = {
        'users_log': Profile.objects.filter(user = request.user).exists(),
        'profile_view': True,
        'Active': profile.isActive,
        'uses': profile.uses
    }

    return render(request, 'users/profile.html', context)