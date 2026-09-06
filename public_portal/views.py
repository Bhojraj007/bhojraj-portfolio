from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType
from django.utils.timesince import timesince
from private_portal.models import Photo, Video, Blog, Comment
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

    # Fetch comments
    blog_ct = ContentType.objects.get_for_model(Blog)
    comments = Comment.objects.filter(content_type=blog_ct, object_id=blog.pk).order_by('created_at')

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
        'comments': comments,
        'comments_count': comments.count(),
        'blog_ct_id': blog_ct.id,
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


def add_public_comment(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)

    content_type_str = request.POST.get('content_type', '').strip().lower()
    object_id = request.POST.get('object_id')
    text = request.POST.get('text', '').strip()
    author_name = request.POST.get('author_name', '').strip()
    author_email = request.POST.get('author_email', '').strip()

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or 
        request.GET.get('ajax') == '1' or
        request.POST.get('ajax') == '1' or
        'application/json' in request.headers.get('accept', '')
    )

    if not text:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Comment text cannot be empty.'}, status=400)
        messages.error(request, 'Please write a reflection or comment before submitting.')
        return redirect(request.META.get('HTTP_REFERER', 'public_portal:home'))

    ct = None
    if content_type_str in ('blog', 'article', 'poem'):
        ct = ContentType.objects.get_for_model(Blog)
    elif content_type_str in ('photo', 'image'):
        ct = ContentType.objects.get_for_model(Photo)
    elif content_type_str in ('gallery_item', 'galleryitem', 'artifact'):
        ct = ContentType.objects.get_for_model(GalleryItem)
    elif content_type_str.isdigit():
        ct = ContentType.objects.filter(id=int(content_type_str)).first()

    if not ct or not object_id:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Target object for comment not specified.'}, status=400)
        messages.error(request, 'Target for comment was not found.')
        return redirect(request.META.get('HTTP_REFERER', 'public_portal:home'))

    user = request.user if request.user.is_authenticated else None
    display_author = (user.get_full_name() or user.username) if user else (author_name or 'Anonymous Visitor')
    display_email = user.email if user else author_email

    comment = Comment.objects.create(
        user=user,
        author_name=display_author,
        author_email=display_email,
        content_type=ct,
        object_id=int(object_id),
        text=text
    )

    if author_email:
        record_identified_lead(
            request, 
            name=display_author, 
            email=author_email, 
            phone='', 
            inquiry_type=f'Comment on {content_type_str}', 
            path=request.path
        )

    if is_ajax:
        total_comments = Comment.objects.filter(content_type=ct, object_id=object_id).count()
        return JsonResponse({
            'status': 'ok',
            'message': 'Comment posted successfully!',
            'comment': {
                'id': comment.id,
                'author': comment.display_author,
                'initial': comment.initial,
                'avatar_url': comment.avatar_url,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%b %d, %Y · %I:%M %p'),
                'time_ago': 'Just now',
                'is_staff': comment.user.is_staff if comment.user else False,
            },
            'comments_count': total_comments
        })

    messages.success(request, '✨ Thank you! Your reflection has been published.')
    ref = request.META.get('HTTP_REFERER', '')
    if ref:
        return redirect(ref + ('#comments' if '#comments' not in ref else ''))
    return redirect('public_portal:home')


def get_comments_ajax(request, content_type, object_id):
    ct = None
    ct_str = content_type.strip().lower()
    if ct_str in ('blog', 'article', 'poem'):
        ct = ContentType.objects.get_for_model(Blog)
    elif ct_str in ('photo', 'image'):
        ct = ContentType.objects.get_for_model(Photo)
    elif ct_str in ('gallery_item', 'galleryitem', 'artifact'):
        ct = ContentType.objects.get_for_model(GalleryItem)
    elif ct_str.isdigit():
        ct = ContentType.objects.filter(id=int(ct_str)).first()

    if not ct:
        return JsonResponse({'status': 'error', 'message': 'Invalid content type.'}, status=400)

    comments_qs = Comment.objects.filter(content_type=ct, object_id=object_id).order_by('created_at')
    data = []
    for c in comments_qs:
        data.append({
            'id': c.id,
            'author': c.display_author,
            'initial': c.initial,
            'avatar_url': c.avatar_url,
            'text': c.text,
            'created_at': c.created_at.strftime('%b %d, %Y · %I:%M %p'),
            'time_ago': timesince(c.created_at) + ' ago',
            'is_staff': c.user.is_staff if c.user else False,
        })
    return JsonResponse({
        'status': 'ok',
        'comments': data,
        'count': len(data),
        'content_type': ct_str,
        'object_id': object_id,
    })


def delete_public_comment(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user.is_staff or (request.user.is_authenticated and comment.user == request.user):
        comment.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': 'Comment removed'})
        messages.success(request, 'Comment removed successfully.')
        return redirect(request.META.get('HTTP_REFERER', 'public_portal:home'))
    return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)


def gallery(request):
    category = request.GET.get('category', '').strip()
    
    photos = list(Photo.objects.filter(is_public=True).order_by('-upload_timestamp'))
    videos = Video.objects.filter(is_public=True).order_by('-upload_timestamp')
    gallery_items = list(GalleryItem.objects.filter(is_active=True).order_by('order', 'id'))
    config = SiteConfiguration.objects.first()
    
    # Calculate comment counts
    photo_ct = ContentType.objects.get_for_model(Photo)
    gallery_ct = ContentType.objects.get_for_model(GalleryItem)
    
    photo_counts = dict(Comment.objects.filter(content_type=photo_ct).values('object_id').annotate(c=Count('id')).values_list('object_id', 'c'))
    gallery_counts = dict(Comment.objects.filter(content_type=gallery_ct).values('object_id').annotate(c=Count('id')).values_list('object_id', 'c'))
    
    for p in photos:
        p.comments_count = photo_counts.get(p.pk, 0)
    for g in gallery_items:
        g.comments_count = gallery_counts.get(g.pk, 0)

    total_count = len(photos) + len(gallery_items) + videos.count()
    
    context = {
        'photos': photos,
        'videos': videos,
        'gallery_items': gallery_items,
        'site_config': config,
        'active_category': category,
        'total_count': total_count,
        'photos_count': len(photos),
        'gallery_items_count': len(gallery_items),
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





