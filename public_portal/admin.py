from django.contrib import admin
from .models import Skill, Experience, Education, Project, ContactMessage, GalleryItem, IbiSAPModule, SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand Identity", {
            "fields": ("brand_name",)
        }),
        ("Hero Section", {
            "fields": ("hero_badge_text", "hero_greeting", "hero_title", "hero_subheadline", "hero_image")
        }),
        ("Dynamic Stat Metrics Strip", {
            "fields": (
                ("stat_1_number", "stat_1_title", "stat_1_sub"),
                ("stat_2_number", "stat_2_title", "stat_2_sub"),
                ("stat_3_number", "stat_3_title", "stat_3_sub"),
                ("stat_4_number", "stat_4_title", "stat_4_sub"),
            )
        }),
        ("Dynamic 4 Pillars", {
            "fields": (
                ("pillar_1_title", "pillar_1_desc"),
                ("pillar_2_title", "pillar_2_desc"),
                ("pillar_3_title", "pillar_3_desc"),
                ("pillar_4_title", "pillar_4_desc"),
            )
        }),
        ("About Me Narrative", {
            "fields": ("about_me_lead", "about_me_text_1", "about_me_text_2", "about_me_text_3")
        }),
        ("Contact Details & Social Channels", {
            "fields": ("email_address", "phone_number", "whatsapp_number", "whatsapp_url", "location", "github_url", "linkedin_url", "prakriti_prabhav_url", "ibisap_live_url")
        }),
        ("Resume & CV Document", {
            "fields": ("resume_file", "resume_url")
        }),
        ("Footer", {
            "fields": ("footer_text",)
        }),

    )

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon_class', 'order')
    list_editable = ('order',)
    list_filter = ('category',)
    search_fields = ('name', 'category')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'date_range', 'order')
    list_editable = ('order',)
    search_fields = ('role', 'company')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'institution', 'date_range', 'order')
    list_editable = ('order',)
    search_fields = ('degree', 'institution')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'tags', 'link', 'is_demo_requestable', 'order')
    list_editable = ('is_demo_requestable', 'order')
    list_filter = ('is_demo_requestable',)
    search_fields = ('title', 'tags', 'description')


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'category_label', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'caption', 'tags')

@admin.register(IbiSAPModule)
class IbiSAPModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'is_enterprise_ready', 'is_retail_ready', 'order')
    list_editable = ('order', 'is_enterprise_ready', 'is_retail_ready')
    search_fields = ('title', 'badge', 'description')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'inquiry_type', 'timestamp')
    list_filter = ('inquiry_type', 'timestamp')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('name', 'email', 'phone', 'inquiry_type', 'message', 'timestamp')

