from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User # added for friendship
from friendship.models import Friend, Follow
from api.models import Post, Image, Comment, Author
from .forms import PostForm, UploadImgForm, AddFriendForm, UnFriendUserForm, FriendRequestForm, CommentForm
from rest_framework.decorators import api_view
from django.http import HttpResponse
from api.serializers import PostSerializer
from rest_framework.response import Response





# not a view can be moved elsewhere
#####################################################
def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def get_posts(request):
    latest_post_list = Post.objects.filter(
        Q(visibility='PU') |
        Q(author=Author.objects.get(user=request.user)))
    return latest_post_list


def try_adding_friend(user, friend):

    msg = ""
    try:
        User.objects.get(username=friend)
    except Exception:
        return "Not a valid user, please try again."
    try:
        Follow.objects.add_follower(user, friend)
        msg += "You are now following %s" % friend
    except Exception:
        msg += "You are already following %s" % friend
    try:
        msg += " and waiting for them to accept your request." % friend
    except Exception:
        msg += " and already waiting for a response to your request"
    return msg



def try_remove_relationship(user, friend):
    try:
        friend_id = int(User.objects.get(username=friend).id)
    except Exception:
        return "Not a valid user, please try again."
    msg = ""
    if Follow.objects.remove_follower(user, friend_id):
        msg += "You are no longer following %s" % friend
    else:
        msg += "You are not following %s, so you can't unfollow them." % friend
    if Friend.objects.remove_friend(friend_id, user):
        msg += " You are no longer friends with %s" % friend
    else:
        msg += " You were never friends with %s, I'm sorry :(" % friend
    return msg
#####################################################


def remove_relationship(request, context):
    unfrienduserform_valid = context['unfrienduserform'].is_valid()
    if unfrienduserform_valid:
        friend = context['unfrienduserform'].cleaned_data['username']
        friend = friend.strip()
        if str(friend) is not '':
            context['unfriend_msg'] = try_remove_relationship(
                request.user,
                friend,
            )
    elif not unfrienduserform_valid:
        context['unfriend_msg'] = "Invalid input."
        context['unfrienduserform'] = UnFriendUserForm


def add_relationship(request, context):
    addform_valid = context['addform'].is_valid(),
    if addform_valid:
        friend = context['addform'].cleaned_data['user_choice_field']
        print friend,"suckkk"
        context['addfriend'] = friend
        if friend is not None:
            print "works"
            context['add_msg'] = try_adding_friend(request.user, friend)
    elif not addform_valid:
        context['add_msg'] = "Invalid input"
        context['addform'] = AddFriendForm()

def friend_requests(request, context):
    requests_valid = context['friendrequestform'].is_valid(),
    if requests_valid:
        #friend = context['friendrequestform'].cleaned_data['user_choice_field']
        print context
        #context['addfriend'] = friend



def friend_mgnt(request):

    users = list(map(lambda x:
                     str(x.from_user),
                     Friend.objects.unread_requests(request.user)))
    context = {'friendrequestform': FriendRequestForm(names=users)}
    print context['friendrequestform'],"dick"
    print "fuck",users
    if request.method == "POST":
        context.update({
            'addform': AddFriendForm(request.POST),
            'unfrienduserform': UnFriendUserForm(request.POST),
        })
        remove_relationship(request, context)
        add_relationship(request, context)
        friend_requests(request, context)
        print "shit"
    else:
        context.update({
            'addform': AddFriendForm(),
            'unfrienduserform': UnFriendUserForm(),
        })
    return render(request, 'posts/friend_mgnt.html', context)


def post_mgnt(request):
        latest_post_list = get_posts(request)
        context = {
            'latest_post_list': latest_post_list
        }
        return render(request, 'posts/post_mgnt.html', context)


# prob should change this to a form view
def index(request):
    latest_post_list = get_posts(request)
    latest_img_list = Image.objects.order_by('-published')[:5]
    context = {
        'latest_image_list': latest_img_list,
        'latest_post_list': latest_post_list
    }
    return render(request, 'posts/index.html', context)


# api stuff for the future
# # post_collection
# @api_view(['GET'])
# def index(request):
#     if request.method == 'GET':
#         posts = Post.objects.all()
#         serializer = PostSerializer(posts, many=True)
#         return Response(serializer.data)



def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = Author.objects.get(user=request.user)
            post.published = timezone.now()
            post.save()
            # future ref make to add the namespace ie "posts"
            return redirect('posts:detail', identity=post.pk)
    else:
        form = PostForm()
    return render(request, 'posts/edit_post.html', {'form': form})


def edit_post(request, identity):
    post = get_object_or_404(Post, pk=identity)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = Author.objects.get(user=request.user)
            post.published_date = timezone.now()
            post.save()
            # the "identity" part must be the same as the P<"identity" in url.py
            return redirect('posts:detail', identity=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/edit_post.html', {'form': form})


def delete_post(request, identity):
    latest_post_list = get_posts(request)
    for post in latest_post_list:
        print post.identity 
        if str(post.identity) == str(identity):
            post.delete()
    return redirect('posts:index')


def post_detail(request, identity):
    print identity
    #identity = Post.objects.get(identity=identity).identity
    print identity
    
    post = get_object_or_404(Post, identity='047f6a63-0174-4c69-ac50-633ea1207766')
    print post
    comment = Comment.objects.create(post=post, published=timezone.now())
    comments = Comment.objects.select_related().filter(post=identity)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        cform = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = Author.objects.get(user=request.user)
            post.published_date = timezone.now()
            post.save()
            # the "identity" part must be the same as the P<"identity" in url.py
            return redirect('posts:detail', identity=post.pk)
        elif cform.is_valid():
            comment = cform.save(commit=False)
            comment.published = timezone.now()
            comment.post=post
            comment.save()
            return redirect('posts:detail', identity=post.pk)                
    else:
        form = PostForm(instance=post)
        cform = CommentForm(instance=comment)
    return render(request, 'posts/detail.html', {'post': post, 'comments': comments, 'form': form, 'cform': cform})



# @api_view(['GET'])
# def post_detail(request, identity):
#     try:
#         post = Post.objects.get(identity=identity)
#     except Post.DoesNotExist:
#         return HttpResponse(status=404)

#     if request.method == 'GET':
#         serializer = PostSerializer(post)
#         return Response(serializer.data)




def create_img(request):
    if request.method == 'POST':
        form = UploadImgForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.author = Author.objects.get(user=request.user)
            img.published = timezone.now()
            img.save()
            return redirect('posts:index')
    else:
        form = UploadImgForm()

