from django.contrib import admin
from .models import Photo, Video, DashboardSettings, Post, Blog, Todo, MoodLog, DailyIntention, GratitudeLog, Reaction, Bookmark, PinnedPost, Follow, Moment, Transaction, Comment

class VisibilityAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_public']
    list_filter = ['is_public', 'user']

class PostAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'is_public']
    list_filter = ['is_public', 'user']

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'amount', 'transaction_type', 'date']
    list_filter = ['transaction_type', 'user', 'date']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['display_author', 'content_object', 'text', 'created_at']
    list_filter = ['created_at', 'content_type']
    search_fields = ['text', 'author_name', 'author_email', 'user__username']
    readonly_fields = ['created_at']

admin.site.register(Photo, VisibilityAdmin)
admin.site.register(Video, VisibilityAdmin)

admin.site.register(DashboardSettings)
admin.site.register(Post, PostAdmin)
admin.site.register(Blog, VisibilityAdmin)
admin.site.register(Todo)
admin.site.register(MoodLog)
admin.site.register(DailyIntention)
admin.site.register(GratitudeLog)
admin.site.register(Reaction)
admin.site.register(Bookmark)
admin.site.register(PinnedPost)
admin.site.register(Follow)
admin.site.register(Moment, VisibilityAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Comment, CommentAdmin)

