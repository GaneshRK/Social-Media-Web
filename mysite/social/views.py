from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Post, Comment, Profile, Follow, Like
from .forms import SignUpForm, LoginForm, PostForm, CommentForm, ProfileForm
from django.db.models import Q

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(profile__bio__icontains=query)
        ).distinct()

    return render(request, 'social/search_results.html', {'users': users, 'query': query})


# 🏠 FEED PAGE
@login_required
def feed(request):
    # Get all the users that the logged-in user follows
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)

    # Show posts by followed users + the user's own posts
    posts = Post.objects.filter(author__in=list(following_users) + [request.user]).order_by('-created_at')

    return render(request, 'social/feed.html', {'posts': posts})

# 📝 SIGNUP VIEW
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)  # create profile automatically
            messages.success(request, 'Account created successfully!')
            return redirect('social:login')
    else:
        form = SignUpForm()
    return render(request, 'social/signup.html', {'form': form})


# 🔐 LOGIN VIEW
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('social:feed')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, "social/login.html", {"form": form})


# 🚪 LOGOUT VIEW
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have logged out.')
    return redirect('social:login')


# 👤 PROFILE VIEW
@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)  # ✅ now defined properly

    posts = Post.objects.filter(author=user).order_by('-created_at')  # ✅ use author instead of user

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()

    context = {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
    }
    return render(request, 'social/profile.html', context)


# ⚙️ EDIT PROFILE
@login_required
def edit_profile(request, username):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('social:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'social/edit_profile.html', {'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)  # don't save yet
            post.author = request.user     # ✅ assign the logged-in user
            post.save()                    # now save
            return redirect('social:feed')
    else:
        form = PostForm()
    return render(request, 'social/create_post.html', {'form': form})

# 💬 POST DETAIL + COMMENTS
@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('-created_at')
    is_liked = Like.objects.filter(post=post, user=request.user).exists()

    # Handle new comment
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            new_comment.save()
            return redirect('social:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'form': form,
    }
    return render(request, 'social/post_detail.html', context)


@login_required
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    # Prevent following self
    if target_user == request.user:
        messages.warning(request, "You can't follow yourself!")
        return redirect('social:profile', username=username)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        # Already following → unfollow
        follow.delete()
        messages.info(request, f"You unfollowed {target_user.username}.")
    else:
        messages.success(request, f"You followed {target_user.username}.")

    return redirect('social:profile', username=username)

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'like_count': post.likes.count()})
    
    return redirect('social:feed')
