from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from private_portal.models import Blog
from public_portal.models import Project

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['public_portal:home', 'public_portal:blog_list', 'public_portal:gallery', 'public_portal:ibisap']

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return Blog.objects.filter(is_public=True).order_by('-created_at')


    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('public_portal:blog_detail', kwargs={'slug': obj.slug})
