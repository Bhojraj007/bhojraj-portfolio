from django.contrib import admin
from .models import Photo, Video, DashboardSettings, Post, Blog, Todo, MoodLog, DailyIntention, GratitudeLog, Reaction, Bookmark, PinnedPost, Follow, Moment, Transaction

class VisibilityAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_public']
    list_filter = ['is_public', 'user']

class PostAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'is_public']
    list_filter = ['is_public', 'user']

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'amount', 'transaction_type', 'date']
    list_filter = ['transaction_type', 'user', 'date']

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
