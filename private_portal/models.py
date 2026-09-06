import os
import datetime
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone

class Photo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='photos/')
    is_public = models.BooleanField(default=False)
    upload_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-upload_timestamp', '-id']

    def __str__(self):
        return self.title

class Video(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos/')
    is_public = models.BooleanField(default=False)
    upload_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-upload_timestamp', '-id']

    def __str__(self):
        return self.title



class DashboardSettings(models.Model):
    background_image = models.ImageField(upload_to='dashboard_bgs/', blank=True, null=True, help_text="Upload a custom background for the private dashboard.")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, help_text="Upload a custom profile picture.")
    
    class Meta:
        verbose_name = "Dashboard Settings"
        verbose_name_plural = "Dashboard Settings"

    def __str__(self):
        return "Private Dashboard Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one settings object exists
        if not self.pk and DashboardSettings.objects.exists():
            # if you'll not check for self.pk 
            # then error will also raised in update of exists model
            return
        return super(DashboardSettings, self).save(*args, **kwargs)

class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Memory / Post"
        verbose_name_plural = "Memories / Posts"

    def __str__(self):
        return f"Memory on {self.created_at.strftime('%Y-%m-%d')}"

from django.utils.text import slugify

class Blog(models.Model):
    CATEGORY_CHOICES = (
        ('poem', '✍️ Poem & Poetry'),
        ('tech', '💻 Tech & Engineering'),
        ('reflection', '🌿 Reflections & Life'),
        ('story', '📖 Story & Narrative'),
        ('thoughts', '💡 Thoughts & Ideas'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True, blank=True, null=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='poem')
    subtitle = models.CharField(max_length=300, blank=True, help_text="Short subtitle or poetic hook")
    excerpt = models.TextField(blank=True, help_text="Brief summary/snippet for cards and SEO")
    content = models.TextField(help_text="Full post content or poem verses (newlines preserved)")
    cover_image = models.ImageField(upload_to='blogs/covers/', blank=True, null=True)
    tags = models.CharField(max_length=300, blank=True, help_text="Comma-separated tags e.g. Poetry, Life, Nepali, Philosophy")
    is_public = models.BooleanField(default=True, help_text="Visible to public visitors")
    is_featured = models.BooleanField(default=False, help_text="Pin to featured section on Home & Blog")
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) if self.title else "piece"
            if not base_slug:
                base_slug = f"post-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            unique_slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        if not self.excerpt and self.content:
            self.excerpt = self.content[:160].strip() + ("..." if len(self.content) > 160 else "")
        super().save(*args, **kwargs)

    @property
    def read_time(self):
        words = len(self.content.split()) if self.content else 0
        if self.category == 'poem':
            return "2 min read" if words < 150 else f"{max(1, round(words / 70))} min read"
        minutes = max(1, round(words / 180))
        return f"{minutes} min read"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class Todo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    TODO_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TODO_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='portal_comments')
    author_name = models.CharField(max_length=150, blank=True, default='')
    author_email = models.EmailField(blank=True, default='')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    @property
    def display_author(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.author_name or 'Anonymous Visitor'

    @property
    def avatar_url(self):
        if self.user and hasattr(self.user, 'profile_picture') and self.user.profile_picture:
            return self.user.profile_picture.url
        return None

    @property
    def initial(self):
        name = self.display_author.strip()
        return name[0].upper() if name else 'A'

    def __str__(self):
        return f"{self.display_author} on {self.content_object}"

class MoodLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    MOOD_CHOICES = (
        ('happy', '😊 Happy'),
        ('calm', '😌 Calm'),
        ('focused', '🧠 Focused'),
        ('tired', '😴 Tired'),
        ('sad', '😔 Sad'),
        ('inspired', '✨ Inspired'),
    )
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    note = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class DailyIntention(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    intention = models.CharField(max_length=255)
    is_met = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def __str__(self):
        return f"{self.user.username}'s Intention for {self.created_at}"

class GratitudeLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Gratitude from {self.created_at}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to='messages/images/', blank=True, null=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ""

    def __str__(self):
        return f"From {self.sender} to {self.recipient} at {self.timestamp}"


class Reaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    REACTION_TYPES = (
        ('love', '❤️ Love'),
    )
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES, default='love')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', 'reaction_type')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} {self.reaction_type} on {self.content_object}"


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.content_object}"


class PinnedPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pinned_posts')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} pinned {self.content_object}"


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='actions', on_delete=models.CASCADE)
    verb = models.CharField(max_length=255) # e.g., 'loved', 'followed', 'messaged'
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor} {self.verb} {self.recipient}"


class Moment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moments')
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='moments/', blank=True, null=True)
    video = models.FileField(upload_to='moments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + datetime.timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Moment at {self.created_at}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    CATEGORY_CHOICES = (
        ('salary', 'Salary'),
        ('freelance', 'Freelance'),
        ('investment', 'Investment'),
        ('gift', 'Gift'),
        ('other_income', 'Other Income'),
        ('housing', 'Housing & Rent'),
        ('food', 'Food & Dining'),
        ('transportation', 'Transportation'),
        ('utilities', 'Utilities'),
        ('insurance', 'Insurance'),
        ('healthcare', 'Healthcare'),
        ('saving', 'Savings & Investments'),
        ('personal', 'Personal & Entertainment'),
        ('education', 'Education'),
        ('other_expense', 'Other Expense'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()}: ${self.amount}"
