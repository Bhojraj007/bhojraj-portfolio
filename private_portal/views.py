import datetime
import nepali_datetime
import random
import json
import csv
from itertools import chain
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, DeleteView, UpdateView
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages

from .models import Photo, Video, DashboardSettings, Post, Blog, Todo, Comment, MoodLog, DailyIntention, GratitudeLog, Message, Reaction, Bookmark, PinnedPost, Follow, Notification, Moment, Transaction
from public_portal.models import (
    Skill, Experience, Education, Project, ContactMessage, GalleryItem, 
    IbiSAPModule, IbiSAPConfiguration, IbiSAPScreenshot, IbiSAPComparisonRow, SiteConfiguration, VisitorLog
)




User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/dashboard.html'
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        action = request.POST.get('action')
        
        if action == 'set_intention':
            intention_text = request.POST.get('intention', '').strip()
            if intention_text:
                today = datetime.date.today()
                DailyIntention.objects.update_or_create(
                    user=request.user, # Added user missing in previous code
                    created_at=today,
                    defaults={'intention': intention_text}
                )
        
        elif action == 'log_mood':
            mood = request.POST.get('mood')
            note = request.POST.get('note', '').strip()
            if mood:
                MoodLog.objects.create(user=request.user, mood=mood, note=note)
                
        elif action == 'toggle_intention':
            intention_id = request.POST.get('intention_id')
            if intention_id:
                try:
                    obj = DailyIntention.objects.get(pk=intention_id, user=request.user)
                    obj.is_met = not obj.is_met
                    obj.save()
                except DailyIntention.DoesNotExist:
                    pass
        
        elif action == 'log_gratitude':
            text = request.POST.get('gratitude', '').strip()
            if text:
                GratitudeLog.objects.create(user=request.user, text=text)

        return redirect('private_portal:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = datetime.date.today()
        
        # Daily Intention
        context['daily_intention'] = DailyIntention.objects.filter(user=user, created_at=today).first()
        
        # Gratitude (Today)
        context['today_gratitude'] = GratitudeLog.objects.filter(user=user, created_at=today).first()
        
        # Streak Calculation (Already handled below at line 281)
        # context['streak'] = get_streak_helper(user)
        
        # Stories (Sanctuary Moments from all followed + own)
        now = timezone.now()
        context['stories'] = Moment.objects.filter(user=user, expires_at__gt=now).order_by('-created_at')
        
        # Flashback (Random memory from > 7 days ago)
        week_ago = today - datetime.timedelta(days=7)
        past_items = list(Post.objects.filter(user=user, created_at__lt=week_ago)) + \
                    list(Photo.objects.filter(user=user, upload_timestamp__lt=week_ago)) + \
                    list(Blog.objects.filter(user=user, created_at__lt=week_ago))
        
        if past_items:
            fb = random.choice(past_items)
            # Robust Date Extraction for Flashback
            date_fields = ['upload_timestamp', 'publication_date', 'watch_date', 'date', 'created_at']
            fb.feed_date = None
            for field in date_fields:
                if hasattr(fb, field):
                    fb.feed_date = getattr(fb, field)
                    break
            
            if not fb.feed_date:
                fb.feed_date = today

            # Expert Metadata: Flashback Age
            days_ago = (today - (fb.feed_date.date() if isinstance(fb.feed_date, datetime.datetime) else fb.feed_date)).days
            if days_ago >= 365:
                years = days_ago // 365
                fb.flashback_age = f"{years} years ago" if years > 1 else "One year ago"
            else:
                fb.flashback_age = f"{days_ago} days ago"
            
            # Format flashback nepali date
            try:
                d = fb.feed_date.date() if isinstance(fb.feed_date, datetime.datetime) else fb.feed_date
                fb.nepali_date = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
            except Exception:
                fb.nepali_date = "Ancient Echo"
            
            # Feed type mapping for template
            if hasattr(fb, 'upload_timestamp'): fb.feed_type = 'photo'
            elif hasattr(fb, 'video'): fb.feed_type = 'video'
            elif hasattr(fb, 'content') and len(fb.content) > 1000: fb.feed_type = 'blog'
            else: fb.feed_type = 'post'
            
            context['flashback'] = fb
            
        # Mood Analytics (Last 30 days)
        last_30 = today - datetime.timedelta(days=30)
        mood_logs = MoodLog.objects.filter(user=user, created_at__gte=last_30)
        total_moods = mood_logs.count()
        
        mood_analytics = []
        if total_moods > 0:
            counts = {}
            for m in mood_logs:
                counts[m.mood] = counts.get(m.mood, 0) + 1
            
            # Map of mood to display info
            mood_info = {
                'happy': {'color': '#10b981', 'label': 'Joyful', 'emoji': '😊'},
                'calm': {'color': '#3b82f6', 'label': 'Serene', 'emoji': '😌'},
                'focused': {'color': '#8b5cf6', 'label': 'Alpha', 'emoji': '🧠'},
                'inspired': {'color': '#f59e0b', 'label': 'Divine', 'emoji': '✨'},
                'tired': {'color': '#64748b', 'label': 'Weary', 'emoji': '😴'},
                'sad': {'color': '#ef4444', 'label': 'Gloom', 'emoji': '😔'},
            }
            
            for m_code, info in mood_info.items():
                count = counts.get(m_code, 0)
                if count > 0:
                    mood_analytics.append({
                        'code': m_code,
                        'name': info['label'],
                        'emoji': info['emoji'],
                        'color': info['color'],
                        'count': count,
                        'percent': round((count / total_moods) * 100)
                    })
            
            # Sort by percentage descending
            mood_analytics.sort(key=lambda x: x['percent'], reverse=True)
            
        context['mood_analytics'] = mood_analytics
        context['recent_moods'] = mood_logs.order_by('-created_at')[:12]
        context['MoodLog'] = MoodLog
        
        # Pending Todos
        context['pending_todos'] = Todo.objects.filter(user=user, status='pending')
        
        # Dashboard Stats (Required by Stats Summary)
        context['post_count'] = Post.objects.filter(user=user).count()
        context['blog_count'] = Blog.objects.filter(user=user).count()
        context['photo_count'] = Photo.objects.filter(user=user).count()
        context['video_count'] = Video.objects.filter(user=user).count()
        context['todo_count'] = Todo.objects.filter(user=user).count()
        
        # Base queries for all content types
        content_groups = [
            (Photo.objects.filter(user=user), 'photo', 'upload_timestamp'),
            (Video.objects.filter(user=user), 'video', 'upload_timestamp'),
            (Post.objects.filter(user=user), 'post', 'created_at'),
            (Blog.objects.filter(user=user), 'blog', 'created_at'),
            (Todo.objects.filter(user=user), 'todo', 'created_at'),
        ]
        
        def get_date(item):
            d = getattr(item, 'feed_date', None)
            if not d: return datetime.date.min
            if hasattr(d, 'date'): return d.date()
            return d

        query = self.request.GET.get('q', '').strip().lower()
        items = []
        for qs, ftype, date_attr in content_groups:
            q_items = list(qs)
            for item in q_items:
                item.feed_type = ftype
                item.feed_date = getattr(item, date_attr)
            
            if query:
                is_num = query.isdigit()
                if ftype == 'post': 
                    q_items = [i for i in q_items if query in i.content.lower() or (is_num and i.id == int(query))]
                elif ftype == 'todo': 
                    q_items = [i for i in q_items if query in i.title.lower() or (is_num and i.id == int(query))]
                else: 
                    q_items = [i for i in q_items if (hasattr(i, 'title') and i.title and query in i.title.lower()) or (hasattr(i, 'content') and i.content and query in i.content.lower()) or (hasattr(i, 'description') and i.description and query in i.description.lower()) or (is_num and i.id == int(query))]
            
            items.extend(q_items)

        feed_items = sorted(items, key=get_date, reverse=True)
        if not query:
            feed_items = feed_items[:30]

        # Get Pinned Item
        pinned_obj = PinnedPost.objects.filter(user=user).first()
        pinned_item = None
        if pinned_obj:
            pinned_item = pinned_obj.content_object
            if pinned_item:
                pinned_item.is_pinned = True
                # Standardize pinned item metadata for template and logic
                pinned_item.feed_type = pinned_item._meta.model_name
                date_attr = 'upload_timestamp' if hasattr(pinned_item, 'upload_timestamp') else \
                            ('publication_date' if hasattr(pinned_item, 'publication_date') else \
                            ('watch_date' if hasattr(pinned_item, 'watch_date') else \
                            ('date' if hasattr(pinned_item, 'date') else 'created_at')))
                pinned_item.feed_date = getattr(pinned_item, date_attr, None)
                
                # Remove from general feed to prevent duplicates
                feed_items = [i for i in feed_items if not (i.id == pinned_item.id and i.feed_type == pinned_item.feed_type)]

        # Attach Metadata (Nepali date, Comments, Reaction info)
        for item in feed_items + ([pinned_item] if pinned_item else []):
            if item.feed_date and item.feed_date.year > 1900:
                d = item.feed_date.date() if isinstance(item.feed_date, datetime.datetime) else item.feed_date
                try:
                    item.nepali_date = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
                except Exception:
                    item.nepali_date = "Resonance Date"
            else:
                item.nepali_date = ""
                
            ct = ContentType.objects.get_for_model(item)
            item.content_type_id = ct.id
            item.comments = Comment.objects.filter(content_type=ct, object_id=item.pk).order_by('created_at')
            item.love_count = Reaction.objects.filter(content_type=ct, object_id=item.pk, reaction_type='love').count()
            item.user_loved = Reaction.objects.filter(user=user, content_type=ct, object_id=item.pk, reaction_type='love').exists()
            item.is_bookmarked = Bookmark.objects.filter(user=user, content_type=ct, object_id=item.pk).exists()

        context['feed_items'] = feed_items
        context['pinned_item'] = pinned_item
        context['search_query'] = query if query else ""
        
        # Inbox logic
        all_msgs = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-timestamp')
        context['unread_count'] = Message.objects.filter(recipient=user, is_read=False).count()
        
        users_chatted = []
        seen_users = set()
        for msg in all_msgs:
            other_user = msg.recipient if msg.sender == user else msg.sender
            if other_user not in seen_users:
                other_user.last_message = msg
                users_chatted.append(other_user)
                seen_users.add(other_user)
        context['conversations'] = users_chatted
        context['streak'] = get_streak_helper(user)

        # Stats
        context['photo_count'] = Photo.objects.filter(user=user).count()
        context['video_count'] = Video.objects.filter(user=user).count()
        context['post_count'] = Post.objects.filter(user=user).count()
        context['blog_count'] = Blog.objects.filter(user=user).count()
        context['todo_count'] = Todo.objects.filter(user=user).count()

        return context

def get_streak_helper(user):
    """Calculates the consecutive days of interaction (posts, logs, or completions)."""
    # Collect all activity dates
    dates = set()
    
    # Fetch raw fields and convert to date objects in Python to avoid __date lookup issues
    post_dates = Post.objects.filter(user=user).values_list('created_at', flat=True)
    mood_dates = MoodLog.objects.filter(user=user).values_list('created_at', flat=True)
    gratitude_dates = GratitudeLog.objects.filter(user=user).values_list('created_at', flat=True)
    intention_dates = DailyIntention.objects.filter(user=user).values_list('created_at', flat=True)

    for d in list(post_dates) + list(mood_dates) + list(gratitude_dates) + list(intention_dates):
        if d:
            if isinstance(d, datetime.datetime):
                dates.add(d.date())
            elif isinstance(d, datetime.date):
                dates.add(d)
    
    # Remove None values if any
    dates.discard(None)
    
    if not dates: return 0
    
    sorted_dates = sorted(list(dates), reverse=True)
    today = datetime.date.today()
    
    streak = 0
    current_date = today
    
    # Check if last interaction was today or yesterday
    if sorted_dates[0] < today - datetime.timedelta(days=1):
        return 0
        
    for d in sorted_dates:
        if d == current_date:
            streak += 1
            current_date -= datetime.timedelta(days=1)
        elif d > current_date:
            continue
        else:
            break
    return streak

class GuardianHubView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'private_portal/profile_form.html'
    fields = ['bio', 'profile_picture', 'background_image']
    success_url = reverse_lazy('private_portal:profile_edit')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Account Intel
        joined_nepali = ''
        if user.date_joined:
            d = user.date_joined.date() if isinstance(user.date_joined, datetime.datetime) else user.date_joined
            try:
                joined_nepali = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
            except Exception:
                joined_nepali = ''

        context['account_info'] = {
            'username': user.username,
            'email': user.email or "No email provided",
            'date_joined': user.date_joined,
            'date_joined_nepali': joined_nepali,
            'last_login': user.last_login,
        }
        
        # Mood Chronicle
        context['mood_history'] = MoodLog.objects.filter(user=user).order_by('-created_at')[:50]
        
        # Sanctuary Stats — rich list with icon/color/link
        stats_config = [
            {'name': 'Photos', 'icon': 'fas fa-camera-retro', 'color': '#10b981', 'count': Photo.objects.filter(user=user).count(), 'link': 'private_portal:photo_list'},
            {'name': 'Videos', 'icon': 'fas fa-video', 'color': '#6366f1', 'count': Video.objects.filter(user=user).count(), 'link': 'private_portal:video_list'},
            {'name': 'Posts', 'icon': 'fas fa-pen-fancy', 'color': '#ec4899', 'count': Post.objects.filter(user=user).count(), 'link': 'private_portal:post_list'},
            {'name': 'Blogs', 'icon': 'fas fa-feather-alt', 'color': '#a78bfa', 'count': Blog.objects.filter(user=user).count(), 'link': 'private_portal:blog_list'},
            {'name': 'Todos', 'icon': 'fas fa-tasks', 'color': '#f59e0b', 'count': Todo.objects.filter(user=user).count(), 'link': 'private_portal:todo_list'},
        ]
        context['stats'] = stats_config
        context['total_content'] = sum(s['count'] for s in stats_config)
        
        # Quick Portals — same structure for template convenience
        context['quick_portals'] = [
            {'name': 'Photos', 'icon': 'fas fa-camera-retro', 'color': '#10b981', 'add_link': 'private_portal:photo_add', 'list_link': 'private_portal:photo_list', 'desc': 'Capture visual fragments'},
            {'name': 'Videos', 'icon': 'fas fa-video', 'color': '#6366f1', 'add_link': 'private_portal:video_add', 'list_link': 'private_portal:video_list', 'desc': 'Store motion memories'},
            {'name': 'Posts', 'icon': 'fas fa-pen-fancy', 'color': '#ec4899', 'add_link': 'private_portal:post_add', 'list_link': 'private_portal:post_list', 'desc': 'Write quick memories'},
            {'name': 'Blogs', 'icon': 'fas fa-feather-alt', 'color': '#a78bfa', 'add_link': 'private_portal:blog_add', 'list_link': 'private_portal:blog_list', 'desc': 'Compose thoughtful echoes'},
            {'name': 'Todos', 'icon': 'fas fa-tasks', 'color': '#f59e0b', 'add_link': 'private_portal:todo_add', 'list_link': 'private_portal:todo_list', 'desc': 'Track personal quests'},
        ]
        
        # Engagement metrics  
        context['total_bookmarks'] = Bookmark.objects.filter(user=user).count()
        context['total_reactions'] = Reaction.objects.filter(user=user).count()
        context['total_comments'] = Comment.objects.filter().count()  # All comments for the user's content
        
        return context

class GuardianPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'private_portal/profile_form.html'
    success_url = reverse_lazy('private_portal:profile_edit')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your resilience (password) has been updated.')
        return super().form_valid(form)

@login_required
@require_POST
def toggle_love(request):
    ct_id = request.POST.get('content_type_id')
    obj_id = request.POST.get('object_id')
    ct = ContentType.objects.get(id=ct_id)
    
    reaction, created = Reaction.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=obj_id,
        reaction_type='love'
    )
    
    if not created:
        reaction.delete()
        action = 'unloved'
    else:
        action = 'loved'
        # Expert Phase: Trigger Notification
        item = reaction.content_object
        if item and hasattr(item, 'user') and item.user and item.user != request.user:
            Notification.objects.get_or_create(
                recipient=item.user,
                actor=request.user,
                verb='loved',
                content_type=ct,
                object_id=obj_id
            )
            
    count = Reaction.objects.filter(content_type=ct, object_id=obj_id, reaction_type='love').count()
    return JsonResponse({'status': 'ok', 'action': action, 'count': count})

@login_required
@require_POST
def toggle_bookmark(request):
    ct_id = request.POST.get('content_type_id')
    obj_id = request.POST.get('object_id')
    ct = ContentType.objects.get(id=ct_id)
    
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=obj_id
    )
    
    if not created:
        bookmark.delete()
        action = 'unbookmarked'
    else:
        action = 'bookmarked'
        
    return JsonResponse({'status': 'ok', 'action': action})

@login_required
@require_POST
def toggle_pin(request):
    ct_id = request.POST.get('content_type_id')
    obj_id = request.POST.get('object_id')
    ct = ContentType.objects.get(id=ct_id)
    
    # Check if this exact post is already pinned
    existing_pin = PinnedPost.objects.filter(user=request.user, content_type=ct, object_id=obj_id).first()
    
    if existing_pin:
        existing_pin.delete()
    else:
        # Remove any other pins first (only one pin at a time)
        PinnedPost.objects.filter(user=request.user).delete()
        PinnedPost.objects.create(user=request.user, content_type=ct, object_id=obj_id)
        
    return redirect('private_portal:dashboard')

class BookmarkListView(LoginRequiredMixin, ListView):
    template_name = 'private_portal/bookmark_list.html'
    context_object_name = 'bookmarked_items'

    def get_queryset(self):
        bookmarks = Bookmark.objects.filter(user=self.request.user).select_related('content_type')
        items = []
        for b in bookmarks:
            item = b.content_object
            if item:
                # Add feed metadata for consistent rendering
                item.feed_type = item._meta.model_name
                
                # Robust date handling
                date_fields = ['upload_timestamp', 'publication_date', 'watch_date', 'date', 'created_at']
                item.feed_date = None
                for field in date_fields:
                    if hasattr(item, field):
                        item.feed_date = getattr(item, field)
                        break
                
                # Fallback to current time if no date found
                if not item.feed_date:
                    item.feed_date = datetime.datetime.now()
                
                # Nepali date
                if item.feed_date and hasattr(item.feed_date, 'year') and item.feed_date.year > 1900:
                    d = item.feed_date.date() if isinstance(item.feed_date, datetime.datetime) else item.feed_date
                    try:
                        item.nepali_date = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
                    except Exception:
                        item.nepali_date = "N/A"
                else:
                    item.nepali_date = "N/A"
                
                # Comments and Content Type for interaction
                ct = ContentType.objects.get_for_model(item)
                item.content_type_id = ct.id
                item.is_bookmarked = True
                item.love_count = Reaction.objects.filter(content_type=ct, object_id=item.pk, reaction_type='love').count()
                item.user_loved = Reaction.objects.filter(user=self.request.user, content_type=ct, object_id=item.pk, reaction_type='love').exists()
                item.comments = Comment.objects.filter(content_type=ct, object_id=item.pk).order_by('created_at')
                items.append(item)
        return items

@login_required
def export_data(request):
    data = {}
    models_to_export = [Photo, Video, Post, Blog, Todo, MoodLog, DailyIntention, GratitudeLog]
    for model in models_to_export:
        queryset = model.objects.filter(user=request.user)
        data[model._meta.verbose_name_plural] = json.loads(serializers.serialize('json', queryset))
    
    response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="sanctuary_export_{request.user.username}.json"'
    return response

@login_required
def clear_all_data(request):
    if request.method == 'POST':
        models_to_clear = [Photo, Video, Post, Blog, Todo, MoodLog, DailyIntention, GratitudeLog, Reaction, Bookmark, PinnedPost]
        for model in models_to_clear:
            model.objects.filter(user=request.user).delete()
        messages.warning(request, "The sanctuary has been reset. All fragments and echoes are gone.")
        return redirect('private_portal:profile_edit')
    return render(request, 'private_portal/confirm_clear.html')

class InboxView(LoginRequiredMixin, ListView):
    template_name = 'private_portal/messenger/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        # Find all users I've chatted with
        messages = Message.objects.filter(Q(sender=self.request.user) | Q(recipient=self.request.user)).order_by('-timestamp')
        users_chatted = []
        seen_users = set()
        for msg in messages:
            other_user = msg.recipient if msg.sender == self.request.user else msg.sender
            if other_user not in seen_users:
                # Get the last message of this conversation
                other_user.last_message = msg
                users_chatted.append(other_user)
                seen_users.add(other_user)
        return users_chatted

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # All users for starting a new chat
        context['all_users'] = User.objects.exclude(id=self.request.user.id)
        return context

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/messenger/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient_id = self.kwargs.get('user_id')
        recipient = User.objects.get(pk=recipient_id)
        context['recipient'] = recipient
        
        # Get all messages between current user and recipient
        messages = Message.objects.filter(
            (Q(sender=self.request.user) & Q(recipient=recipient)) |
            (Q(sender=recipient) & Q(recipient=self.request.user))
        ).order_by('timestamp')
        
        # Mark as read
        Message.objects.filter(sender=recipient, recipient=self.request.user, is_read=False).update(is_read=True)
        
        context['chat_messages'] = messages
        return context

    def post(self, request, *args, **kwargs):
        recipient_id = self.kwargs.get('user_id')
        recipient = User.objects.get(pk=recipient_id)
        body = request.POST.get('body', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        
        if body or image or file:
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                body=body,
                image=image,
                file=file
            )
            # Notify the recipient
            Notification.objects.create(
                recipient=recipient,
                actor=request.user,
                verb='sent you a message'
            )
        
        return redirect('private_portal:chat_detail', user_id=recipient_id)

class BaseMediaListView(LoginRequiredMixin, ListView):
    paginate_by = 12

class BaseMediaCreateView(LoginRequiredMixin, CreateView):
    template_name = 'private_portal/generic_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class BaseMediaUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'private_portal/generic_form.html'

class BaseMediaDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'private_portal/confirm_delete.html'


# Photo Views
class PhotoListView(BaseMediaListView):
    model = Photo
    template_name = 'private_portal/photo_list.html'

class PhotoCreateView(BaseMediaCreateView):
    model = Photo
    fields = ['title', 'description', 'image', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class PhotoUpdateView(BaseMediaUpdateView):
    model = Photo
    fields = ['title', 'description', 'image', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class PhotoDeleteView(BaseMediaDeleteView):
    model = Photo
    success_url = reverse_lazy('private_portal:dashboard')

# Video Views
class VideoListView(BaseMediaListView):
    model = Video
    template_name = 'private_portal/video_list.html'

class VideoCreateView(BaseMediaCreateView):
    model = Video
    fields = ['title', 'description', 'video', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class VideoUpdateView(BaseMediaUpdateView):
    model = Video
    fields = ['title', 'description', 'video', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class VideoDeleteView(BaseMediaDeleteView):
    model = Video
    success_url = reverse_lazy('private_portal:dashboard')

# Post Views
class PostListView(BaseMediaListView):
    model = Post
    template_name = 'private_portal/post_list.html'
    ordering = ['-created_at']

class PostCreateView(BaseMediaCreateView):
    model = Post
    fields = ['content', 'image', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class PostUpdateView(BaseMediaUpdateView):
    model = Post
    fields = ['content', 'image', 'is_public']
    success_url = reverse_lazy('private_portal:dashboard')

class PostDeleteView(BaseMediaDeleteView):
    model = Post
    success_url = reverse_lazy('private_portal:dashboard')

# Blog Views
class BlogListView(BaseMediaListView):
    model = Blog
    template_name = 'private_portal/blog_list.html'
    ordering = ['-created_at']

    def get_queryset(self):
        return Blog.objects.filter(user=self.request.user).order_by('-created_at')

class BlogCreateView(BaseMediaCreateView):
    model = Blog
    fields = ['title', 'category', 'subtitle', 'excerpt', 'content', 'cover_image', 'tags', 'is_featured', 'is_public']
    success_url = reverse_lazy('private_portal:blog_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Write New Poem / Blog'
        context['button_text'] = 'Publish Post'
        return context

class BlogUpdateView(BaseMediaUpdateView):
    model = Blog
    fields = ['title', 'category', 'subtitle', 'excerpt', 'content', 'cover_image', 'tags', 'is_featured', 'is_public']
    success_url = reverse_lazy('private_portal:blog_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Poem / Blog'
        context['button_text'] = 'Save Changes'
        return context

class BlogDeleteView(BaseMediaDeleteView):
    model = Blog
    success_url = reverse_lazy('private_portal:blog_list')


# Todo Views
class TodoListView(BaseMediaListView):
    model = Todo
    template_name = 'private_portal/todo_list.html'
    ordering = ['-created_at']

class TodoCreateView(BaseMediaCreateView):
    model = Todo
    fields = ['title', 'description', 'status']
    success_url = reverse_lazy('private_portal:dashboard')

class TodoUpdateView(BaseMediaUpdateView):
    model = Todo
    fields = ['title', 'description', 'status']
    success_url = reverse_lazy('private_portal:dashboard')

class TodoDeleteView(BaseMediaDeleteView):
    model = Todo
    success_url = reverse_lazy('private_portal:dashboard')

def add_comment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        ct_id = request.POST.get('content_type_id')
        obj_id = request.POST.get('object_id')
        text = request.POST.get('text', '').strip()
        
        if ct_id and obj_id and text:
            ct = ContentType.objects.get(id=ct_id)
            Comment.objects.create(
                content_type=ct,
                object_id=obj_id,
                text=text,
                user=request.user
            )
    return redirect('private_portal:dashboard')


@login_required
def chat_poll(request, user_id):
    """AJAX endpoint for polling new messages in a chat."""
    last_id = int(request.GET.get('last_id', 0))
    recipient = get_object_or_404(User, pk=user_id)
    
    new_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user)),
        pk__gt=last_id
    ).order_by('timestamp')
    
    # Mark received messages as read
    Message.objects.filter(sender=recipient, recipient=request.user, is_read=False).update(is_read=True)
    
    messages_data = []
    for msg in new_messages:
        msg_data = {
            'id': msg.id,
            'body': msg.body,
            'is_mine': msg.sender == request.user,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_read': msg.is_read,
        }
        if msg.image:
            msg_data['image_url'] = msg.image.url
        if msg.file:
            msg_data['file_url'] = msg.file.url
            msg_data['file_name'] = msg.filename
        messages_data.append(msg_data)
    
    return JsonResponse({
        'messages': messages_data,
        'unread_count': Message.objects.filter(recipient=request.user, is_read=False).count()
    })


class PulseView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/social/pulse.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get users I follow
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        # Show own posts + posts from people followed
        allowed_users = list(following_ids) + [user.id]

        content_groups = [
            (Photo.objects.filter(user_id__in=allowed_users), 'photo', 'upload_timestamp'),
            (Video.objects.filter(user_id__in=allowed_users), 'video', 'upload_timestamp'),
            (Post.objects.filter(user_id__in=allowed_users), 'post', 'created_at'),
            (Blog.objects.filter(user_id__in=allowed_users), 'blog', 'created_at'),
            (Todo.objects.filter(user_id__in=allowed_users), 'todo', 'created_at'),
        ]
        
        # Moments (Stories) - Active only
        now = timezone.now()
        moments = Moment.objects.filter(
            user_id__in=allowed_users,
            expires_at__gt=now
        ).select_related('user')
        context['active_moments'] = moments

        items = []
        for qs, ftype, date_attr in content_groups:
            q_items = list(qs)
            final_q_items = []
            for item in q_items:
                # Show if it's mine OR if it's public AND from someone I follow
                if item.user == user or getattr(item, 'is_public', False):
                    item.feed_type = ftype
                    item.feed_date = getattr(item, date_attr)
                    final_q_items.append(item)
            items.extend(final_q_items)

        def get_sort_key(item):
            d = item.feed_date
            if not d: return datetime.datetime.min
            if isinstance(d, datetime.datetime): return d
            return datetime.datetime.combine(d, datetime.time.min)

        feed_items = sorted(items, key=get_sort_key, reverse=True)[:50]

        # Attach Metadata
        for item in feed_items:
            if item.feed_date and item.feed_date.year > 1900:
                d = item.feed_date.date() if isinstance(item.feed_date, datetime.datetime) else item.feed_date
                try:
                    item.nepali_date = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
                except Exception:
                    item.nepali_date = "N/A"
            else:
                item.nepali_date = "N/A"
            
            ct = ContentType.objects.get_for_model(item)
            item.content_type_id = ct.id
            item.love_count = Reaction.objects.filter(content_type=ct, object_id=item.pk, reaction_type='love').count()
            item.user_loved = Reaction.objects.filter(user=user, content_type=ct, object_id=item.pk, reaction_type='love').exists()
            item.is_bookmarked = Bookmark.objects.filter(user=user, content_type=ct, object_id=item.pk).exists()

        # Community Analytics (Global)
        all_logs_24h = MoodLog.objects.filter(created_at__gte=timezone.now() - datetime.timedelta(hours=24))
        global_counts = {}
        for l in all_logs_24h: global_counts[l.mood] = global_counts.get(l.mood, 0) + 1
        
        total_global = sum(global_counts.values())
        global_vibe = []
        if total_global > 0:
            mood_info = {
                'happy': {'color': '#10b981', 'label': 'Joyful'},
                'calm': {'color': '#3b82f6', 'label': 'Serene'},
                'focused': {'color': '#8b5cf6', 'label': 'Alpha'},
                'inspired': {'color': '#f59e0b', 'label': 'Divine'},
                'tired': {'color': '#64748b', 'label': 'Weary'},
                'sad': {'color': '#ef4444', 'label': 'Gloom'},
            }
            for m, count in global_counts.items():
                if m in mood_info:
                    global_vibe.append({
                        'label': mood_info[m]['label'],
                        'color': mood_info[m]['color'],
                        'percent': (count / total_global * 100)
                    })
            global_vibe.sort(key=lambda x: x['percent'], reverse=True)
        context['global_vibe'] = global_vibe
        
        # Trending Fragments (Public, High Love, Last 7 days)
        last_week = timezone.now() - datetime.timedelta(days=7)
        trending = []
        # Querying Reactions directly to find high-love public objects
        top_reactions = Reaction.objects.filter(reaction_type='love', created_at__gte=last_week)\
                                      .values('content_type', 'object_id')\
                                      .annotate(count=Count('id'))\
                                      .order_by('-count')[:3]
        
        for tr in top_reactions:
            try:
                ct = ContentType.objects.get_for_id(tr['content_type'])
                obj = ct.get_object_for_this_type(pk=tr['object_id'])
                if hasattr(obj, 'is_public') and obj.is_public:
                    obj.feed_type = ct.model
                    obj.love_count = tr['count']
                    # Standardize title for template
                    if hasattr(obj, 'title') and obj.title: obj.display_title = obj.title
                    elif hasattr(obj, 'movie_title') and obj.movie_title: obj.display_title = obj.movie_title
                    else: obj.display_title = f"Public {ct.model.title()}"
                    trending.append(obj)
            except Exception:
                continue
        context['trending_fragments'] = trending
        
        # Velocity and Guardians
        context['velocity'] = Post.objects.filter(is_public=True, created_at__gte=timezone.now()-datetime.timedelta(hours=24)).count() + \
                           Photo.objects.filter(is_public=True, upload_timestamp__gte=timezone.now()-datetime.timedelta(hours=24)).count()
        
        suggested = list(User.objects.exclude(id=user.id).exclude(followers__follower=user)[:5])
        for s in suggested:
            s.streak = get_streak_helper(s)
        context['suggested_guardians'] = suggested
        
        return context

class GuardianProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/social/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        target_user = get_object_or_404(User, username=username)
        user = self.request.user

        context['target_user'] = target_user
        context['is_following'] = Follow.objects.filter(follower=user, following=target_user).exists()
        context['follower_count'] = Follow.objects.filter(following=target_user).count()
        context['following_count'] = Follow.objects.filter(follower=target_user).count()

        # Only public items for other users
        # If it's my own profile, maybe I want to see everything? 
        # But the user said "different user have different dashboard", so let's keep it public-facing.
        is_owner = (target_user == user)

        content_groups = [
            (Photo.objects.filter(user=target_user), 'photo', 'upload_timestamp'),
            (Video.objects.filter(user=target_user), 'video', 'upload_timestamp'),
            (Post.objects.filter(user=target_user), 'post', 'created_at'),
            (Blog.objects.filter(user=target_user), 'blog', 'created_at'),
            (Todo.objects.filter(user=target_user), 'todo', 'created_at'),
        ]
        
        items = []
        for qs, ftype, date_attr in content_groups:
            q_items = list(qs)
            
            # Use Python-level filtering to avoid FieldError on models without is_public
            if not is_owner:
                q_items = [item for item in q_items if getattr(item, 'is_public', False)]
            for item in q_items:
                item.feed_type = ftype
                item.feed_date = getattr(item, date_attr)
                
                # Add metadata similarly to Pulse
                if item.feed_date and item.feed_date.year > 1900:
                    d = item.feed_date.date() if isinstance(item.feed_date, datetime.datetime) else item.feed_date
                    try:
                        item.nepali_date = nepali_datetime.date.from_datetime_date(d).strftime('%B %d, %Y')
                    except Exception:
                        item.nepali_date = "N/A"
                else:
                    item.nepali_date = "N/A"
                
                items.append(item)

        def get_sort_key(item):
            d = item.feed_date
            if not d: return datetime.datetime.min
            if isinstance(d, datetime.datetime): return d
            return datetime.datetime.combine(d, datetime.time.min)

        context['feed_items'] = sorted(items, key=get_sort_key, reverse=True)

        # Get active moments for the user
        from django.utils import timezone
        active_moments = Moment.objects.filter(user=target_user, expires_at__gt=timezone.now())
        if not is_owner:
            active_moments = active_moments.filter(is_public=True)
        context['active_moments'] = active_moments

        # Get follower/following users for modal
        context['followers_list'] = [f.follower for f in Follow.objects.filter(following=target_user)]
        context['following_list'] = [f.following for f in Follow.objects.filter(follower=target_user)]

        return context

@login_required
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot follow yourself'})
    
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        follow.delete()
        action = 'unfollowed'
    else:
        action = 'followed'
        # Expert Phase: Trigger Notification
        Notification.objects.get_or_create(
            recipient=target_user,
            actor=request.user,
            verb='followed'
        )
    
    return JsonResponse({'status': 'ok', 'action': action, 'count': Follow.objects.filter(following=target_user).count()})

@login_required
def search_guardians(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search users
    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query)
    ).exclude(id=request.user.id)[:5]
    
    results = []
    for u in users:
        results.append({
            'type': 'guardian',
            'id': u.id,
            'title': u.username,
            'url': f"/private/guardian/{u.username}/",
            'subtitle': 'Guardian',
            'is_following': Follow.objects.filter(follower=request.user, following=u).exists(),
            'streak': 0 # Defaulting for search to avoid heavy compute
        })
        try:
            results[-1]['streak'] = get_streak_helper(u)
        except:
            pass
        
    # Search public fragments
    public_photos = Photo.objects.filter(is_public=True, title__icontains=query)[:3]
    for p in public_photos:
        results.append({
            'type': 'fragment',
            'title': p.title,
            'url': f"/private/photos/",
            'subtitle': f'Fragment by {p.user.username}'
        })
        
    return JsonResponse({'results': results})

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user)[:10]
    data = []
    for n in notifications:
        data.append({
            'actor': n.actor.username,
            'verb': n.verb,
            'timestamp': n.timestamp.strftime('%B %d, %H:%M'),
            'is_read': n.is_read
        })
    return JsonResponse({
        'notifications': data, 
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })

class MomentCreateView(LoginRequiredMixin, CreateView):
    model = Moment
    fields = ['title', 'image', 'video', 'is_public']
    template_name = 'private_portal/social/moment_add.html'
    success_url = reverse_lazy('private_portal:pulse')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@login_required
@require_POST
def toggle_visibility(request, ct_id, obj_id):
    ct = get_object_or_404(ContentType, id=ct_id)
    model_class = ct.model_class()
    obj = get_object_or_404(model_class, id=obj_id, user=request.user)
    
    obj.is_public = not obj.is_public
    obj.save()
    return JsonResponse({'status': 'ok', 'is_public': obj.is_public})

from django.db.models import Sum

# --- Cash Book Integration ---

class CashBookView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/cashbook/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Transactions processing
        transactions = Transaction.objects.filter(user=user).order_by('-date', '-id')
        
        total_income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        total_expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        balance = total_income - total_expense
        
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        monthly_txs = transactions.filter(date__year=current_year, date__month=current_month)
        monthly_income = monthly_txs.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        monthly_expense = monthly_txs.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        
        # Categories breakdown
        categories = transactions.filter(transaction_type='expense').values('category').annotate(total=Sum('amount')).order_by('-total')
        for cat in categories:
            cat['display'] = dict(Transaction.CATEGORY_CHOICES).get(cat['category'], cat['category'])
            cat['percentage'] = round((cat['total'] / total_expense) * 100) if total_expense else 0
        
        context['transactions'] = transactions[:20]
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['balance'] = balance
        context['monthly_income'] = monthly_income
        context['monthly_expense'] = monthly_expense
        context['categories_breakdown'] = categories
        return context

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    fields = ['title', 'amount', 'transaction_type', 'category', 'date', 'description']
    template_name = 'private_portal/generic_form.html'
    success_url = reverse_lazy('private_portal:cashbook_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.is_public = False # Force private
        return super().form_valid(form)

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    fields = ['title', 'amount', 'transaction_type', 'category', 'date', 'description']
    template_name = 'private_portal/generic_form.html'
    success_url = reverse_lazy('private_portal:cashbook_dashboard')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'private_portal/confirm_delete.html'
    success_url = reverse_lazy('private_portal:cashbook_dashboard')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

@login_required
def export_cashbook_csv(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cashbook_export_{request.user.username}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Title', 'Amount', 'Description'])
    
    for tx in transactions:
        writer.writerow([
            tx.date,
            tx.get_transaction_type_display(),
            tx.get_category_display(),
            tx.title,
            tx.amount,
            tx.description
        ])
        
    return response

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'private_portal/global_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        user = self.request.user
        
        results = []
        if query:
            # Search all personal content
            photos = Photo.objects.filter(user=user).filter(Q(title__icontains=query) | Q(description__icontains=query))
            videos = Video.objects.filter(user=user).filter(Q(title__icontains=query) | Q(description__icontains=query))
            posts = Post.objects.filter(user=user, content__icontains=query)
            blogs = Blog.objects.filter(user=user).filter(Q(title__icontains=query) | Q(content__icontains=query))
            todos = Todo.objects.filter(user=user).filter(Q(title__icontains=query) | Q(description__icontains=query))
            transactions = Transaction.objects.filter(user=user).filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query))
            
            # Pack results with types
            for p in photos: results.append({'obj': p, 'type': 'Photo', 'url': reverse_lazy('private_portal:photo_edit', args=[p.id]), 'date': p.upload_timestamp, 'icon': 'fas fa-image', 'color': '#10b981'})
            for v in videos: results.append({'obj': v, 'type': 'Video', 'url': reverse_lazy('private_portal:video_edit', args=[v.id]), 'date': v.upload_timestamp, 'icon': 'fas fa-video', 'color': '#ef4444'})
            for p in posts: results.append({'obj': p, 'type': 'Memory', 'url': reverse_lazy('private_portal:post_edit', args=[p.id]), 'date': p.created_at, 'icon': 'fas fa-pen-fancy', 'color': '#f59e0b'})
            for b in blogs: results.append({'obj': b, 'type': 'Blog', 'url': reverse_lazy('private_portal:blog_edit', args=[b.id]), 'date': b.created_at, 'icon': 'fas fa-feather-alt', 'color': '#ec4899'})
            for t in todos: results.append({'obj': t, 'type': 'Task', 'url': reverse_lazy('private_portal:todo_edit', args=[t.id]), 'date': t.created_at, 'icon': 'fas fa-check-circle', 'color': '#14b8a6'})
            for tx in transactions: results.append({'obj': tx, 'type': 'Ledger', 'url': reverse_lazy('private_portal:transaction_edit', args=[tx.id]), 'date': tx.date, 'icon': 'fas fa-wallet', 'color': '#10b981'})
            
            # Sort by date descending safely
            def get_sort_date(item):
                d = item['date']
                if not d: return datetime.datetime.min
                if isinstance(d, datetime.datetime): return d
                return datetime.datetime.combine(d, datetime.time.min)
                
            results.sort(key=get_sort_date, reverse=True)
            
        context['search_query'] = query
        context['results'] = results
        context['result_count'] = len(results)
        return context


# ================================================================
#  SITE MANAGER — Admin Features in Private Portal
# ================================================================

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires the user to be staff."""
    def test_func(self):
        return self.request.user.is_staff


class SiteManagerView(StaffRequiredMixin, TemplateView):
    template_name = 'private_portal/site_manager/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_count'] = Blog.objects.count()
        context['skill_count'] = Skill.objects.count()
        context['experience_count'] = Experience.objects.count()
        context['education_count'] = Education.objects.count()
        context['project_count'] = Project.objects.count()
        context['gallery_count'] = GalleryItem.objects.count()
        context['module_count'] = IbiSAPModule.objects.count()
        context['screenshot_count'] = IbiSAPScreenshot.objects.count()
        context['comparison_count'] = IbiSAPComparisonRow.objects.count()
        context['inquiry_count'] = ContactMessage.objects.count()
        context['recent_inquiries'] = ContactMessage.objects.all()[:5]
        context['config'] = SiteConfiguration.objects.first()
        context['visitor_count'] = VisitorLog.objects.count()
        context['lead_count'] = VisitorLog.objects.filter(is_lead=True).count()
        return context




class SiteConfigEditView(StaffRequiredMixin, TemplateView):
    template_name = 'private_portal/site_manager/config_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config, _ = SiteConfiguration.objects.get_or_create(pk=1)
        context['config'] = config
        return context

    def post(self, request, *args, **kwargs):
        config, _ = SiteConfiguration.objects.get_or_create(pk=1)
        fields = [
            'brand_name',
            'hero_badge_text', 'hero_greeting', 'hero_title', 'hero_subheadline',
            'stat_1_number', 'stat_1_title', 'stat_1_sub',
            'stat_2_number', 'stat_2_title', 'stat_2_sub',
            'stat_3_number', 'stat_3_title', 'stat_3_sub',
            'stat_4_number', 'stat_4_title', 'stat_4_sub',
            'pillar_1_title', 'pillar_1_desc',
            'pillar_2_title', 'pillar_2_desc',
            'pillar_3_title', 'pillar_3_desc',
            'pillar_4_title', 'pillar_4_desc',
            'about_me_lead', 'about_me_text_1', 'about_me_text_2', 'about_me_text_3',
            'email_address', 'phone_number', 'whatsapp_number', 'whatsapp_url', 'location',
            'github_url', 'linkedin_url', 'prakriti_prabhav_url', 'ibisap_live_url',
            'resume_url', 'footer_text',
        ]
        for field in fields:
            val = request.POST.get(field)
            if val is not None:
                setattr(config, field, val)
        if 'hero_image' in request.FILES:
            config.hero_image = request.FILES['hero_image']
        if 'resume_file' in request.FILES:
            config.resume_file = request.FILES['resume_file']
        config.save()
        messages.success(request, 'Site configuration updated successfully.')
        return redirect('private_portal:site_config_edit')




# --- Generic CRUD Pattern for Public Portal Models ---

class SmSkillListView(StaffRequiredMixin, ListView):
    model = Skill
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'skill'
        context['content_title'] = 'Skills'
        context['content_icon'] = 'fas fa-code'
        context['add_url'] = 'private_portal:sm_skill_add'
        context['edit_url'] = 'private_portal:sm_skill_edit'
        context['delete_url'] = 'private_portal:sm_skill_delete'
        context['columns'] = ['Name', 'Category', 'Icon', 'Order']
        context['fields'] = ['name', 'category', 'icon_class', 'order']
        return context


class SmSkillCreateView(StaffRequiredMixin, CreateView):
    model = Skill
    fields = ['name', 'category', 'icon_class', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_skill_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Skill'
        context['content_icon'] = 'fas fa-code'
        context['back_url'] = 'private_portal:sm_skill_list'
        return context


class SmSkillUpdateView(StaffRequiredMixin, UpdateView):
    model = Skill
    fields = ['name', 'category', 'icon_class', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_skill_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Skill'
        context['content_icon'] = 'fas fa-code'
        context['back_url'] = 'private_portal:sm_skill_list'
        context['is_edit'] = True
        return context


class SmSkillDeleteView(StaffRequiredMixin, DeleteView):
    model = Skill
    success_url = reverse_lazy('private_portal:sm_skill_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Skill'
        context['back_url'] = 'private_portal:sm_skill_list'
        return context


# Experience CRUD
class SmExperienceListView(StaffRequiredMixin, ListView):
    model = Experience
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'experience'
        context['content_title'] = 'Experience'
        context['content_icon'] = 'fas fa-briefcase'
        context['add_url'] = 'private_portal:sm_experience_add'
        context['edit_url'] = 'private_portal:sm_experience_edit'
        context['delete_url'] = 'private_portal:sm_experience_delete'
        context['columns'] = ['Role', 'Company', 'Date Range', 'Order']
        context['fields'] = ['role', 'company', 'date_range', 'order']
        return context


class SmExperienceCreateView(StaffRequiredMixin, CreateView):
    model = Experience
    fields = ['role', 'company', 'date_range', 'description', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_experience_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Experience'
        context['content_icon'] = 'fas fa-briefcase'
        context['back_url'] = 'private_portal:sm_experience_list'
        return context


class SmExperienceUpdateView(StaffRequiredMixin, UpdateView):
    model = Experience
    fields = ['role', 'company', 'date_range', 'description', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_experience_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Experience'
        context['content_icon'] = 'fas fa-briefcase'
        context['back_url'] = 'private_portal:sm_experience_list'
        context['is_edit'] = True
        return context


class SmExperienceDeleteView(StaffRequiredMixin, DeleteView):
    model = Experience
    success_url = reverse_lazy('private_portal:sm_experience_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Experience'
        context['back_url'] = 'private_portal:sm_experience_list'
        return context


# Education CRUD
class SmEducationListView(StaffRequiredMixin, ListView):
    model = Education
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'education'
        context['content_title'] = 'Education'
        context['content_icon'] = 'fas fa-graduation-cap'
        context['add_url'] = 'private_portal:sm_education_add'
        context['edit_url'] = 'private_portal:sm_education_edit'
        context['delete_url'] = 'private_portal:sm_education_delete'
        context['columns'] = ['Degree', 'Institution', 'Date Range', 'Order']
        context['fields'] = ['degree', 'institution', 'date_range', 'order']
        return context


class SmEducationCreateView(StaffRequiredMixin, CreateView):
    model = Education
    fields = ['degree', 'institution', 'date_range', 'description', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_education_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Education'
        context['content_icon'] = 'fas fa-graduation-cap'
        context['back_url'] = 'private_portal:sm_education_list'
        return context


class SmEducationUpdateView(StaffRequiredMixin, UpdateView):
    model = Education
    fields = ['degree', 'institution', 'date_range', 'description', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_education_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Education'
        context['content_icon'] = 'fas fa-graduation-cap'
        context['back_url'] = 'private_portal:sm_education_list'
        context['is_edit'] = True
        return context


class SmEducationDeleteView(StaffRequiredMixin, DeleteView):
    model = Education
    success_url = reverse_lazy('private_portal:sm_education_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Education'
        context['back_url'] = 'private_portal:sm_education_list'
        return context


# Project CRUD
class SmProjectListView(StaffRequiredMixin, ListView):
    model = Project
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'project'
        context['content_title'] = 'Projects'
        context['content_icon'] = 'fas fa-rocket'
        context['add_url'] = 'private_portal:sm_project_add'
        context['edit_url'] = 'private_portal:sm_project_edit'
        context['delete_url'] = 'private_portal:sm_project_delete'
        context['columns'] = ['Title', 'Tags', 'Link', 'Demo Enabled', 'Order']
        context['fields'] = ['title', 'tags', 'link', 'is_demo_requestable', 'order']
        return context


class SmProjectCreateView(StaffRequiredMixin, CreateView):
    model = Project
    fields = ['title', 'description', 'tags', 'link', 'image', 'is_demo_requestable', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_project_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Project'
        context['content_icon'] = 'fas fa-rocket'
        context['back_url'] = 'private_portal:sm_project_list'
        return context


class SmProjectUpdateView(StaffRequiredMixin, UpdateView):
    model = Project
    fields = ['title', 'description', 'tags', 'link', 'image', 'is_demo_requestable', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_project_list')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Project'
        context['content_icon'] = 'fas fa-rocket'
        context['back_url'] = 'private_portal:sm_project_list'
        context['is_edit'] = True
        return context


class SmProjectDeleteView(StaffRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('private_portal:sm_project_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Project'
        context['back_url'] = 'private_portal:sm_project_list'
        return context


# Gallery CRUD
class SmGalleryListView(StaffRequiredMixin, ListView):
    model = GalleryItem
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'gallery'
        context['content_title'] = 'Gallery Items'
        context['content_icon'] = 'fas fa-photo-video'
        context['add_url'] = 'private_portal:sm_gallery_add'
        context['edit_url'] = 'private_portal:sm_gallery_edit'
        context['delete_url'] = 'private_portal:sm_gallery_delete'
        context['columns'] = ['Title', 'Category', 'Active', 'Order']
        context['fields'] = ['title', 'category', 'is_active', 'order']
        return context


class SmGalleryCreateView(StaffRequiredMixin, CreateView):
    model = GalleryItem
    fields = ['title', 'category', 'category_label', 'image', 'static_image_path', 'caption', 'tags', 'order', 'is_active']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_gallery_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Gallery Item'
        context['content_icon'] = 'fas fa-photo-video'
        context['back_url'] = 'private_portal:sm_gallery_list'
        return context


class SmGalleryUpdateView(StaffRequiredMixin, UpdateView):
    model = GalleryItem
    fields = ['title', 'category', 'category_label', 'image', 'static_image_path', 'caption', 'tags', 'order', 'is_active']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_gallery_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Gallery Item'
        context['content_icon'] = 'fas fa-photo-video'
        context['back_url'] = 'private_portal:sm_gallery_list'
        context['is_edit'] = True
        return context


class SmGalleryDeleteView(StaffRequiredMixin, DeleteView):
    model = GalleryItem
    success_url = reverse_lazy('private_portal:sm_gallery_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Gallery Item'
        context['back_url'] = 'private_portal:sm_gallery_list'
        return context


# IbiSAP Module CRUD
class SmIbiSAPModuleListView(StaffRequiredMixin, ListView):
    model = IbiSAPModule
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type'] = 'ibisap_module'
        context['content_title'] = 'IbiSAP Modules'
        context['content_icon'] = 'fas fa-cubes'
        context['add_url'] = 'private_portal:sm_ibisap_module_add'
        context['edit_url'] = 'private_portal:sm_ibisap_module_edit'
        context['delete_url'] = 'private_portal:sm_ibisap_module_delete'
        context['columns'] = ['Title', 'Badge', 'Enterprise', 'Retail', 'Order']
        context['fields'] = ['title', 'badge', 'is_enterprise_ready', 'is_retail_ready', 'order']
        return context


class SmIbiSAPModuleCreateView(StaffRequiredMixin, CreateView):
    model = IbiSAPModule
    fields = ['title', 'badge', 'description', 'icon_class', 'image', 'static_image_path', 'is_enterprise_ready', 'is_retail_ready', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_module_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add IbiSAP Module'
        context['content_icon'] = 'fas fa-cubes'
        context['back_url'] = 'private_portal:sm_ibisap_module_list'
        return context


class SmIbiSAPModuleUpdateView(StaffRequiredMixin, UpdateView):
    model = IbiSAPModule
    fields = ['title', 'badge', 'description', 'icon_class', 'image', 'static_image_path', 'is_enterprise_ready', 'is_retail_ready', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_module_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit IbiSAP Module'
        context['content_icon'] = 'fas fa-cubes'
        context['back_url'] = 'private_portal:sm_ibisap_module_list'
        context['is_edit'] = True
        return context


class SmIbiSAPModuleDeleteView(StaffRequiredMixin, DeleteView):
    model = IbiSAPModule
    success_url = reverse_lazy('private_portal:sm_ibisap_module_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'IbiSAP Module'
        context['back_url'] = 'private_portal:sm_ibisap_module_list'
        return context


# ================================================================
#  IBISAP GLOBAL CONFIGURATION & PRICING
# ================================================================
class SmIbiSAPConfigEditView(StaffRequiredMixin, UpdateView):
    model = IbiSAPConfiguration
    fields = [
        'hero_badge', 'hero_title', 'hero_description', 'live_sandbox_url', 'live_sandbox_btn_text',
        'metric_1_val', 'metric_1_lbl',
        'metric_2_val', 'metric_2_lbl',
        'metric_3_val', 'metric_3_lbl',
        'metric_4_val', 'metric_4_lbl',
        'enterprise_title', 'enterprise_tagline', 'enterprise_desc', 'enterprise_features',
        'retail_title', 'retail_tagline', 'retail_desc', 'retail_features',
        'cta_headline', 'cta_subheadline'
    ]
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:site_manager')

    def get_object(self, queryset=None):
        obj = IbiSAPConfiguration.objects.first()
        if not obj:
            obj = IbiSAPConfiguration.objects.create()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'IbiSAP ERP Global Content & Pricing Topologies'
        context['content_icon'] = 'fas fa-sliders-h'
        context['back_url'] = 'private_portal:site_manager'
        context['is_edit'] = True
        return context


# ================================================================
#  IBISAP SCREENSHOTS SHOWCASE
# ================================================================
class SmIbiSAPScreenshotListView(StaffRequiredMixin, ListView):
    model = IbiSAPScreenshot
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'IbiSAP Interface Showcase'
        context['content_icon'] = 'fas fa-desktop'
        context['add_url'] = 'private_portal:sm_ibisap_screenshot_add'
        context['edit_url'] = 'private_portal:sm_ibisap_screenshot_edit'
        context['delete_url'] = 'private_portal:sm_ibisap_screenshot_delete'
        context['columns'] = ['Title', 'Category', 'Description', 'Order', 'Active']
        context['fields'] = ['title', 'category_tag', 'description', 'order', 'is_active']
        return context


class SmIbiSAPScreenshotCreateView(StaffRequiredMixin, CreateView):
    model = IbiSAPScreenshot
    fields = ['title', 'category_tag', 'description', 'image', 'static_image_path', 'order', 'is_active']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_screenshot_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add IbiSAP Interface Showcase'
        context['content_icon'] = 'fas fa-desktop'
        context['back_url'] = 'private_portal:sm_ibisap_screenshot_list'
        return context


class SmIbiSAPScreenshotUpdateView(StaffRequiredMixin, UpdateView):
    model = IbiSAPScreenshot
    fields = ['title', 'category_tag', 'description', 'image', 'static_image_path', 'order', 'is_active']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_screenshot_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit IbiSAP Interface Showcase'
        context['content_icon'] = 'fas fa-desktop'
        context['back_url'] = 'private_portal:sm_ibisap_screenshot_list'
        context['is_edit'] = True
        return context


class SmIbiSAPScreenshotDeleteView(StaffRequiredMixin, DeleteView):
    model = IbiSAPScreenshot
    success_url = reverse_lazy('private_portal:sm_ibisap_screenshot_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'IbiSAP Interface'
        context['back_url'] = 'private_portal:sm_ibisap_screenshot_list'
        return context


# ================================================================
#  IBISAP COMPARISON MATRIX
# ================================================================
class SmIbiSAPComparisonListView(StaffRequiredMixin, ListView):
    model = IbiSAPComparisonRow
    template_name = 'private_portal/site_manager/content_list.html'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'IbiSAP Comparison Matrix Rows'
        context['content_icon'] = 'fas fa-table'
        context['add_url'] = 'private_portal:sm_ibisap_comparison_add'
        context['edit_url'] = 'private_portal:sm_ibisap_comparison_edit'
        context['delete_url'] = 'private_portal:sm_ibisap_comparison_delete'
        context['columns'] = ['Feature / Spec', 'Enterprise Value', 'Retail Value', 'Order']
        context['fields'] = ['feature_name', 'enterprise_value', 'retail_value', 'order']
        return context



class SmIbiSAPComparisonCreateView(StaffRequiredMixin, CreateView):
    model = IbiSAPComparisonRow
    fields = ['feature_name', 'enterprise_value', 'retail_value', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_comparison_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Add Comparison Matrix Row'
        context['content_icon'] = 'fas fa-table'
        context['back_url'] = 'private_portal:sm_ibisap_comparison_list'
        return context


class SmIbiSAPComparisonUpdateView(StaffRequiredMixin, UpdateView):
    model = IbiSAPComparisonRow
    fields = ['feature_name', 'enterprise_value', 'retail_value', 'order']
    template_name = 'private_portal/site_manager/content_form.html'
    success_url = reverse_lazy('private_portal:sm_ibisap_comparison_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Edit Comparison Matrix Row'
        context['content_icon'] = 'fas fa-table'
        context['back_url'] = 'private_portal:sm_ibisap_comparison_list'
        context['is_edit'] = True
        return context


class SmIbiSAPComparisonDeleteView(StaffRequiredMixin, DeleteView):
    model = IbiSAPComparisonRow
    success_url = reverse_lazy('private_portal:sm_ibisap_comparison_list')
    template_name = 'private_portal/site_manager/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = 'Comparison Matrix Row'
        context['back_url'] = 'private_portal:sm_ibisap_comparison_list'
        return context



# Contact Messages / Inquiries (Read-only)
class SmInquiryListView(StaffRequiredMixin, ListView):
    model = ContactMessage
    template_name = 'private_portal/site_manager/inquiry_list.html'
    context_object_name = 'inquiries'
    paginate_by = 20


# Visitor Intelligence, Leads & Monetization Analytics
class AnalyticsDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'private_portal/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        req = self.request.GET
        period = req.get('period', 'all').strip()
        lead_filter = req.get('lead_filter', 'all').strip()
        device_filter = req.get('device', 'all').strip()
        source_filter = req.get('source', 'all').strip()
        search_query = req.get('q', '').strip()

        now = timezone.now()
        base_qs = VisitorLog.objects.all()

        # Date Range Filter
        if period == 'today':
            base_qs = base_qs.filter(created_at__gte=now - datetime.timedelta(hours=24))
        elif period == '7d':
            base_qs = base_qs.filter(created_at__gte=now - datetime.timedelta(days=7))
        elif period == '30d':
            base_qs = base_qs.filter(created_at__gte=now - datetime.timedelta(days=30))

        # Device Filter
        if device_filter == 'mobile':
            base_qs = base_qs.filter(device_type__icontains='Mobile')
        elif device_filter == 'desktop':
            base_qs = base_qs.filter(device_type='Desktop')
        elif device_filter == 'tablet':
            base_qs = base_qs.filter(device_type='Tablet')
        elif device_filter == 'bot':
            base_qs = base_qs.filter(device_type__icontains='Bot')

        # Source / Referrer Filter
        if source_filter == 'google':
            base_qs = base_qs.filter(referrer_domain__icontains='Google')
        elif source_filter == 'direct':
            base_qs = base_qs.filter(referrer_domain__icontains='Direct')
        elif source_filter == 'linkedin':
            base_qs = base_qs.filter(referrer_domain__icontains='LinkedIn')
        elif source_filter == 'facebook':
            base_qs = base_qs.filter(referrer_domain__icontains='Facebook')
        elif source_filter == 'github':
            base_qs = base_qs.filter(referrer_domain__icontains='GitHub')

        # Lead Type Filter
        if lead_filter == 'leads_only':
            base_qs = base_qs.filter(is_lead=True)
        elif lead_filter == 'enterprise_only':
            base_qs = base_qs.filter(is_lead=True, inquiry_intent__icontains='Demo')

        # Keyword Search
        if search_query:
            base_qs = base_qs.filter(
                Q(visitor_name__icontains=search_query) |
                Q(visitor_email__icontains=search_query) |
                Q(visitor_phone__icontains=search_query) |
                Q(ip_address__icontains=search_query) |
                Q(country__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(path__icontains=search_query) |
                Q(inquiry_intent__icontains=search_query)
            )

        # Global Counters (All-time context)
        last_24h = now - datetime.timedelta(hours=24)
        last_15m = now - datetime.timedelta(minutes=15)
        total_hits = VisitorLog.objects.count()
        unique_visitors = VisitorLog.objects.values('ip_address').distinct().count()
        hits_24h = VisitorLog.objects.filter(created_at__gte=last_24h).count()
        active_live = VisitorLog.objects.filter(created_at__gte=last_15m).values('ip_address').distinct().count()

        # Filtered Counters
        filtered_total_hits = base_qs.count()
        filtered_unique_visitors = base_qs.values('ip_address').distinct().count()

        # Leads & Monetization
        all_leads_qs = VisitorLog.objects.filter(is_lead=True).exclude(visitor_name__isnull=True).order_by('-created_at')
        total_leads_count = all_leads_qs.values('visitor_email').distinct().count()
        inquiries_count = ContactMessage.objects.count()
        demo_count = ContactMessage.objects.filter(Q(inquiry_type__icontains='Demo') | Q(inquiry_type__icontains='IbiSAP')).count()
        
        # Enterprise Lead Tiers
        est_commercial_pipeline = (demo_count * 1500) + ((inquiries_count - demo_count) * 500)
        if est_commercial_pipeline == 0 and inquiries_count > 0:
            est_commercial_pipeline = inquiries_count * 500

        conversion_rate = round((total_leads_count / unique_visitors * 100), 1) if unique_visitors > 0 else 0.0

        # Top Pages & Referrers within filter
        top_pages = base_qs.values('path').annotate(hits=Count('id')).order_by('-hits')[:8]
        top_referrers = base_qs.values('referrer_domain').annotate(count=Count('id')).order_by('-count')[:6]
        top_countries = base_qs.values('country').annotate(count=Count('id')).order_by('-count')[:6]
        device_stats = base_qs.values('device_type').annotate(count=Count('id')).order_by('-count')

        # Identified Leads list
        identified_leads = []
        seen_emails = set()
        for log in all_leads_qs:
            email_key = (log.visitor_email or log.visitor_name or '').lower().strip()
            if email_key and email_key not in seen_emails:
                seen_emails.add(email_key)
                identified_leads.append(log)
            if len(identified_leads) >= 40:
                break

        # Recent Live Traffic Stream
        recent_traffic = base_qs.order_by('-created_at')[:60]

        context.update({
            'total_hits': total_hits,
            'unique_visitors': unique_visitors,
            'hits_24h': hits_24h,
            'active_live': active_live,
            'filtered_total_hits': filtered_total_hits,
            'filtered_unique_visitors': filtered_unique_visitors,
            'total_leads_count': total_leads_count,
            'inquiries_count': inquiries_count,
            'demo_count': demo_count,
            'conversion_rate': conversion_rate,
            'est_commercial_pipeline': est_commercial_pipeline,
            'top_pages': top_pages,
            'top_referrers': top_referrers,
            'top_countries': top_countries,
            'device_stats': device_stats,
            'identified_leads': identified_leads,
            'recent_traffic': recent_traffic,
            # Filter state
            'period': period,
            'lead_filter': lead_filter,
            'device_filter': device_filter,
            'source_filter': source_filter,
            'search_query': search_query,
        })
        return context


@login_required
def export_leads_csv(request):
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rajabhoj_leads_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Client / Visitor Name',
        'Gmail / Email',
        'Phone Number',
        'Inquiry Intent / Tier',
        'Country',
        'City',
        'IP Address',
        'Visit Frequency',
        'Est. Value ($)',
        'First Captured Timestamp'
    ])

    leads_qs = VisitorLog.objects.filter(is_lead=True).exclude(visitor_name__isnull=True).order_by('-created_at')
    seen = set()
    for l in leads_qs:
        key = (l.visitor_email or l.visitor_name or '').lower().strip()
        if key not in seen:
            seen.add(key)
            writer.writerow([
                l.visitor_name or 'N/A',
                l.visitor_email or 'N/A',
                l.visitor_phone or 'N/A',
                l.inquiry_intent or 'General Commercial Inquiry',
                l.country or 'Nepal',
                l.city or 'N/A',
                l.ip_address,
                l.visit_count,
                float(l.estimated_value or 500.00),
                l.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

    return response


@login_required
def purge_bot_traffic(request):
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=403)
    
    deleted_count, _ = VisitorLog.objects.filter(
        Q(device_type__icontains='Bot') | 
        Q(user_agent__icontains='bot') | 
        Q(user_agent__icontains='crawler') | 
        Q(user_agent__icontains='spider')
    ).delete()
    
    messages.success(request, f'🧹 Successfully purged {deleted_count} automated bot and crawler log entries.')
    return redirect('private_portal:analytics_dashboard')


