from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, F
from private_portal.models import Photo, Video, Blog
from .models import (
    Skill, 
    Experience, 
    Education, 
    Project, 
    ContactMessage, 
    GalleryItem, 
    IbiSAPModule,
    IbiSAPConfiguration,
    IbiSAPScreenshot,
    IbiSAPComparisonRow,
    SiteConfiguration,
    VisitorLog
)


def record_identified_lead(request, name, email, phone, inquiry_type, path):
    try:
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or ''
        request.session['visitor_lead_name'] = name
        request.session['visitor_lead_email'] = email
        request.session['visitor_lead_phone'] = phone

        is_enterprise = any(k in inquiry_type.lower() for k in ['demo', 'ibisap', 'enterprise', 'sap', 'banking'])
        est_value = 1500.00 if is_enterprise else 500.00

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')

        updated_rows = 0
        if session_key:
            updated_rows = VisitorLog.objects.filter(session_key=session_key).update(
                visitor_name=name,
                visitor_email=email,
                visitor_phone=phone,
                is_lead=True,
                inquiry_intent=inquiry_type,
                estimated_value=est_value
            )

        if updated_rows == 0:
            country = request.META.get('HTTP_CF_IPCOUNTRY') or request.META.get('HTTP_X_COUNTRY_CODE') or 'Nepal'
            VisitorLog.objects.create(
                ip_address=ip[:60],
                session_key=session_key[:100],
                path=path[:255],
                visitor_name=name,
                visitor_email=email,
                visitor_phone=phone,
                is_lead=True,
                inquiry_intent=inquiry_type,
                estimated_value=est_value,
                country=country
            )
    except Exception:
        pass


from .utils import send_lead_email_notification_async

def home(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        inquiry_type = request.POST.get('inquiry_type', 'General Inquiry').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            contact_obj = ContactMessage.objects.create(
                name=name, 
                email=email, 
                phone=phone,
                inquiry_type=inquiry_type,
                message=message
            )
            record_identified_lead(request, name, email, phone, inquiry_type, path='/')
            send_lead_email_notification_async(contact_obj)

            if 'Demo' in inquiry_type or 'IbiSAP' in inquiry_type:
                messages.success(request, f'🎉 Enterprise Demo Request Confirmed for {name}! I will reach out at {email}{" or " + phone if phone else ""} within 6–12 hours.')
            else:
                messages.success(request, f'Transmission received, {name}! Thank you for reaching out. I will get back to you shortly.')

            return redirect('public_portal:home')




    config = SiteConfiguration.objects.first()
    skills = Skill.objects.all()
    experiences = Experience.objects.all()
    educations = Education.objects.all()
    projects = Project.objects.all()
    gallery_items = GalleryItem.objects.filter(is_active=True)
    
    # Recent & Featured Blogs / Poems
    featured_blogs = Blog.objects.filter(is_public=True).order_by('-is_featured', '-created_at')[:3]
    recent_poems = Blog.objects.filter(is_public=True, category='poem').order_by('-created_at')[:2]
    
    context = {
        'site_config': config,
        'skills': skills,
        'experiences': experiences,
        'educations': educations,
        'projects': projects,
        'gallery_items': gallery_items,
        'featured_blogs': featured_blogs,
        'recent_poems': recent_poems,
    }
    return render(request, 'public_portal/home.html', context)


def blog_list(request):
    category = request.GET.get('category', '').strip()
    tag = request.GET.get('tag', '').strip()
    q = request.GET.get('q', '').strip()

    qs = Blog.objects.filter(is_public=True)

    if category:
        qs = qs.filter(category=category)
    if tag:
        qs = qs.filter(tags__icontains=tag)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__icontains=q) | Q(subtitle__icontains=q))

    # All published blogs
    blogs = qs.order_by('-is_featured', '-created_at')
    
    # Hero/Featured article (only when not searching or on specific filter)
    featured_blog = None
    if not category and not tag and not q:
        featured_blog = blogs.filter(is_featured=True).first()
        if not featured_blog and blogs.exists():
            featured_blog = blogs.first()

    # Category counts
    all_public = Blog.objects.filter(is_public=True)
    category_counts = {
        'all': all_public.count(),
        'poem': all_public.filter(category='poem').count(),
        'tech': all_public.filter(category='tech').count(),
        'reflection': all_public.filter(category='reflection').count(),
        'story': all_public.filter(category='story').count(),
        'thoughts': all_public.filter(category='thoughts').count(),
    }

    config = SiteConfiguration.objects.first()

    context = {
        'blogs': blogs,
        'featured_blog': featured_blog,
        'category_counts': category_counts,
        'active_category': category,
        'active_tag': tag,
        'search_query': q,
        'site_config': config,
    }
    return render(request, 'public_portal/blog_list.html', context)


def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug, is_public=True)
    
    # Increment views count
    Blog.objects.filter(pk=blog.pk).update(views_count=F('views_count') + 1)
    blog.refresh_from_db(fields=['views_count'])

    # Related blogs
    related_blogs = Blog.objects.filter(is_public=True, category=blog.category).exclude(pk=blog.pk).order_by('-created_at')[:3]
    if related_blogs.count() < 3:
        extra = Blog.objects.filter(is_public=True).exclude(pk=blog.pk).exclude(pk__in=related_blogs.values_list('pk', flat=True)).order_by('-created_at')[:3 - related_blogs.count()]
        related_blogs = list(related_blogs) + list(extra)

    # Previous and Next blogs
    prev_blog = Blog.objects.filter(is_public=True, created_at__lt=blog.created_at).order_by('-created_at').first()
    next_blog = Blog.objects.filter(is_public=True, created_at__gt=blog.created_at).order_by('created_at').first()

    config = SiteConfiguration.objects.first()

    context = {
        'blog': blog,
        'related_blogs': related_blogs,
        'prev_blog': prev_blog,
        'next_blog': next_blog,
        'site_config': config,
    }
    return render(request, 'public_portal/blog_detail.html', context)


def blog_detail_by_id(request, pk):
    blog = get_object_or_404(Blog, pk=pk, is_public=True)
    if blog.slug:
        return redirect('public_portal:blog_detail', slug=blog.slug)
    return blog_detail(request, slug=blog.slug)


def blog_like(request, blog_id):
    if request.method == 'POST':
        blog = get_object_or_404(Blog, pk=blog_id, is_public=True)
        Blog.objects.filter(pk=blog.pk).update(likes_count=F('likes_count') + 1)
        blog.refresh_from_db(fields=['likes_count'])
        return JsonResponse({'status': 'ok', 'likes': blog.likes_count})
    return JsonResponse({'error': 'POST required'}, status=400)


def ibisap(request):
    """
    Gracefully redirect /ibisap/ requests to the main portfolio projects showcase.
    """
    return redirect('/#projects')


def gallery(request):
    category = request.GET.get('category', '').strip()
    
    photos = Photo.objects.filter(is_public=True).order_by('-upload_timestamp')
    videos = Video.objects.filter(is_public=True).order_by('-upload_timestamp')
    gallery_items = GalleryItem.objects.filter(is_active=True).order_by('order', 'id')
    config = SiteConfiguration.objects.first()
    
    total_count = photos.count() + gallery_items.count() + videos.count()
    
    context = {
        'photos': photos,
        'videos': videos,
        'gallery_items': gallery_items,
        'site_config': config,
        'active_category': category,
        'total_count': total_count,
        'photos_count': photos.count(),
        'gallery_items_count': gallery_items.count(),
        'videos_count': videos.count(),
    }
    return render(request, 'public_portal/gallery.html', context)


def ibisap(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        inquiry_type = request.POST.get('inquiry_type', 'Enterprise IbiSAP Implementation').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            contact_obj = ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                inquiry_type=f"IbiSAP Demo: {inquiry_type}",
                message=message
            )
            record_identified_lead(request, name, email, phone, f"IbiSAP Demo: {inquiry_type}", path='/ibisap/')
            send_lead_email_notification_async(contact_obj)
            messages.success(request, f'🎉 IbiSAP Enterprise Demo Request Confirmed for {name}! We will reach out to {email}{" or " + phone if phone else ""} shortly.')
            return redirect('public_portal:ibisap')



    modules = IbiSAPModule.objects.all().order_by('order', 'id')
    ibisap_config = IbiSAPConfiguration.objects.first()
    if not ibisap_config:
        ibisap_config = IbiSAPConfiguration.objects.create()

    # Parse features into title/desc pairs
    ent_features = []
    for line in (ibisap_config.enterprise_features or '').splitlines():
        if ':' in line:
            title, desc = line.split(':', 1)
            ent_features.append({'title': title.strip(), 'desc': desc.strip()})
        elif line.strip():
            ent_features.append({'title': line.strip(), 'desc': ''})

    ret_features = []
    for line in (ibisap_config.retail_features or '').splitlines():
        if ':' in line:
            title, desc = line.split(':', 1)
            ret_features.append({'title': title.strip(), 'desc': desc.strip()})
        elif line.strip():
            ret_features.append({'title': line.strip(), 'desc': ''})

    screenshots = IbiSAPScreenshot.objects.filter(is_active=True).order_by('order', 'id')
    comparison_rows = IbiSAPComparisonRow.objects.all().order_by('order', 'id')
    config = SiteConfiguration.objects.first()

    return render(request, 'public_portal/ibisap.html', {
        'modules': modules,
        'ibisap_config': ibisap_config,
        'ent_features': ent_features,
        'ret_features': ret_features,
        'screenshots': screenshots,
        'comparison_rows': comparison_rows,
        'site_config': config,
    })





