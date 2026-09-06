from django.urls import path
from . import views

app_name = 'private_portal'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.GuardianHubView.as_view(), name='profile_edit'),
    path('messenger/', views.InboxView.as_view(), name='inbox'),
    path('messenger/<int:user_id>/', views.ChatView.as_view(), name='chat_detail'),
    path('messenger/<int:user_id>/poll/', views.chat_poll, name='chat_poll'),
    path('add-comment/', views.add_comment, name='add_comment'),
    
    # Photo urls
    path('photos/', views.PhotoListView.as_view(), name='photo_list'),
    path('photos/add/', views.PhotoCreateView.as_view(), name='photo_add'),
    path('photos/<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo_edit'),
    path('photos/<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='photo_delete'),
    
    # Video urls
    path('videos/', views.VideoListView.as_view(), name='video_list'),
    path('videos/add/', views.VideoCreateView.as_view(), name='video_add'),
    path('videos/<int:pk>/edit/', views.VideoUpdateView.as_view(), name='video_edit'),
    path('videos/<int:pk>/delete/', views.VideoDeleteView.as_view(), name='video_delete'),
    

    
    # Post urls
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/add/', views.PostCreateView.as_view(), name='post_add'),
    path('posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    
    # Blog urls
    path('blogs/', views.BlogListView.as_view(), name='blog_list'),
    path('blogs/add/', views.BlogCreateView.as_view(), name='blog_add'),
    path('blogs/<int:pk>/edit/', views.BlogUpdateView.as_view(), name='blog_edit'),
    path('blogs/<int:pk>/delete/', views.BlogDeleteView.as_view(), name='blog_delete'),
    
    # Todo urls
    path('todos/', views.TodoListView.as_view(), name='todo_list'),
    path('todos/add/', views.TodoCreateView.as_view(), name='todo_add'),
    path('todos/<int:pk>/edit/', views.TodoUpdateView.as_view(), name='todo_edit'),
    path('todos/<int:pk>/delete/', views.TodoDeleteView.as_view(), name='todo_delete'),
    
    # New Social & Guardian Hub features
    path('toggle-love/', views.toggle_love, name='toggle_love'),
    path('toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('toggle-pin/', views.toggle_pin, name='toggle_pin'),
    path('bookmarks/', views.BookmarkListView.as_view(), name='bookmark_list'),
    path('export-data/', views.export_data, name='export_data'),
    path('clear-data/', views.clear_all_data, name='clear_all_data'),
    path('password-change/', views.GuardianPasswordChangeView.as_view(), name='password_change'),
    
    # Social Expansion
    # Social Expansion Phase 2
    path('pulse/', views.PulseView.as_view(), name='pulse'),
    path('guardian/<str:username>/', views.GuardianProfileView.as_view(), name='guardian_profile'),
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('search/', views.search_guardians, name='search_guardians'),
    path('search/content/', views.GlobalSearchView.as_view(), name='global_search'),
    path('moments/add/', views.MomentCreateView.as_view(), name='moment_add'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('toggle-visibility/<int:ct_id>/<int:obj_id>/', views.toggle_visibility, name='toggle_visibility'),
    
    # Personal Finance: Cash Book Integration
    path('cashbook/', views.CashBookView.as_view(), name='cashbook_dashboard'),
    path('cashbook/add/', views.TransactionCreateView.as_view(), name='transaction_add'),
    path('cashbook/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('cashbook/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('cashbook/export/', views.export_cashbook_csv, name='cashbook_export'),

    # ================================================================
    #  SITE MANAGER — Admin Features in Private Portal
    # ================================================================
    path('site-manager/', views.SiteManagerView.as_view(), name='site_manager'),
    path('site-manager/config/', views.SiteConfigEditView.as_view(), name='site_config_edit'),

    # Skills CRUD
    path('site-manager/skills/', views.SmSkillListView.as_view(), name='sm_skill_list'),
    path('site-manager/skills/add/', views.SmSkillCreateView.as_view(), name='sm_skill_add'),
    path('site-manager/skills/<int:pk>/edit/', views.SmSkillUpdateView.as_view(), name='sm_skill_edit'),
    path('site-manager/skills/<int:pk>/delete/', views.SmSkillDeleteView.as_view(), name='sm_skill_delete'),

    # Experience CRUD
    path('site-manager/experience/', views.SmExperienceListView.as_view(), name='sm_experience_list'),
    path('site-manager/experience/add/', views.SmExperienceCreateView.as_view(), name='sm_experience_add'),
    path('site-manager/experience/<int:pk>/edit/', views.SmExperienceUpdateView.as_view(), name='sm_experience_edit'),
    path('site-manager/experience/<int:pk>/delete/', views.SmExperienceDeleteView.as_view(), name='sm_experience_delete'),

    # Education CRUD
    path('site-manager/education/', views.SmEducationListView.as_view(), name='sm_education_list'),
    path('site-manager/education/add/', views.SmEducationCreateView.as_view(), name='sm_education_add'),
    path('site-manager/education/<int:pk>/edit/', views.SmEducationUpdateView.as_view(), name='sm_education_edit'),
    path('site-manager/education/<int:pk>/delete/', views.SmEducationDeleteView.as_view(), name='sm_education_delete'),

    # Projects CRUD
    path('site-manager/projects/', views.SmProjectListView.as_view(), name='sm_project_list'),
    path('site-manager/projects/add/', views.SmProjectCreateView.as_view(), name='sm_project_add'),
    path('site-manager/projects/<int:pk>/edit/', views.SmProjectUpdateView.as_view(), name='sm_project_edit'),
    path('site-manager/projects/<int:pk>/delete/', views.SmProjectDeleteView.as_view(), name='sm_project_delete'),

    # Gallery CRUD
    path('site-manager/gallery/', views.SmGalleryListView.as_view(), name='sm_gallery_list'),
    path('site-manager/gallery/add/', views.SmGalleryCreateView.as_view(), name='sm_gallery_add'),
    path('site-manager/gallery/<int:pk>/edit/', views.SmGalleryUpdateView.as_view(), name='sm_gallery_edit'),
    path('site-manager/gallery/<int:pk>/delete/', views.SmGalleryDeleteView.as_view(), name='sm_gallery_delete'),

    # IbiSAP Dynamic Ecosystem CRUD
    path('site-manager/ibisap-config/', views.SmIbiSAPConfigEditView.as_view(), name='sm_ibisap_config_edit'),

    # IbiSAP Modules CRUD
    path('site-manager/ibisap-modules/', views.SmIbiSAPModuleListView.as_view(), name='sm_ibisap_module_list'),
    path('site-manager/ibisap-modules/add/', views.SmIbiSAPModuleCreateView.as_view(), name='sm_ibisap_module_add'),
    path('site-manager/ibisap-modules/<int:pk>/edit/', views.SmIbiSAPModuleUpdateView.as_view(), name='sm_ibisap_module_edit'),
    path('site-manager/ibisap-modules/<int:pk>/delete/', views.SmIbiSAPModuleDeleteView.as_view(), name='sm_ibisap_module_delete'),

    # IbiSAP Screenshots Showcase CRUD
    path('site-manager/ibisap-screenshots/', views.SmIbiSAPScreenshotListView.as_view(), name='sm_ibisap_screenshot_list'),
    path('site-manager/ibisap-screenshots/add/', views.SmIbiSAPScreenshotCreateView.as_view(), name='sm_ibisap_screenshot_add'),
    path('site-manager/ibisap-screenshots/<int:pk>/edit/', views.SmIbiSAPScreenshotUpdateView.as_view(), name='sm_ibisap_screenshot_edit'),
    path('site-manager/ibisap-screenshots/<int:pk>/delete/', views.SmIbiSAPScreenshotDeleteView.as_view(), name='sm_ibisap_screenshot_delete'),

    # IbiSAP Comparison Matrix CRUD
    path('site-manager/ibisap-comparison/', views.SmIbiSAPComparisonListView.as_view(), name='sm_ibisap_comparison_list'),
    path('site-manager/ibisap-comparison/add/', views.SmIbiSAPComparisonCreateView.as_view(), name='sm_ibisap_comparison_add'),
    path('site-manager/ibisap-comparison/<int:pk>/edit/', views.SmIbiSAPComparisonUpdateView.as_view(), name='sm_ibisap_comparison_edit'),
    path('site-manager/ibisap-comparison/<int:pk>/delete/', views.SmIbiSAPComparisonDeleteView.as_view(), name='sm_ibisap_comparison_delete'),


    # Inquiries & Demo Requests (Full CRUD)
    path('site-manager/inquiries/', views.SmInquiryListView.as_view(), name='sm_inquiry_list'),
    path('site-manager/inquiries/<int:pk>/', views.SmInquiryDetailView.as_view(), name='sm_inquiry_detail'),
    path('site-manager/inquiries/<int:pk>/edit/', views.SmInquiryUpdateView.as_view(), name='sm_inquiry_edit'),
    path('site-manager/inquiries/<int:pk>/delete/', views.SmInquiryDeleteView.as_view(), name='sm_inquiry_delete'),

    # Visitor Telemetry, Leads & Monetization Analytics
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('analytics/export/', views.export_leads_csv, name='analytics_export_leads'),
    path('analytics/purge-bots/', views.purge_bot_traffic, name='analytics_purge_bots'),
    path('site-manager/analytics/', views.AnalyticsDashboardView.as_view(), name='sm_analytics'),
]


