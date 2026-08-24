from django.db import models

class Skill(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, null=True)
    icon_class = models.CharField(max_length=100, blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

class Experience(models.Model):
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    date_range = models.CharField(max_length=100)
    description = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.role} at {self.company}"

class Education(models.Model):
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    date_range = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.degree} at {self.institution}"

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.CharField(max_length=300, help_text="Comma separated tags")
    link = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='portfolio/projects/', blank=True, null=True)
    is_demo_requestable = models.BooleanField(default=False, help_text="Enable 'Request a Demo' button for this project")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True, help_text="Contact Phone / WhatsApp Number")
    inquiry_type = models.CharField(max_length=200, default="General Inquiry", blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Message from {self.name} ({self.inquiry_type})"


class GalleryItem(models.Model):
    CATEGORY_CHOICES = (
        ('ibisap', 'IbiSAP ERP'),
        ('compliance', 'Compliance & CBS'),
        ('workspace', 'Dev & Setup'),
        ('events', 'Events & Leadership'),
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='ibisap')
    category_label = models.CharField(max_length=100, default='IbiSAP ERP')
    image = models.ImageField(upload_to='gallery/', blank=True, null=True)
    static_image_path = models.CharField(max_length=255, blank=True, null=True, help_text="Fallback static path e.g. gallery/ibisap-dashboard.png")
    caption = models.TextField()
    tags = models.CharField(max_length=300, help_text="Comma separated tags", default="Django, ERP, Cloud")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        if self.static_image_path:
            return f"/static/{self.static_image_path}"
        return "/static/gallery/ibisap-dashboard.png"

class IbiSAPModule(models.Model):
    title = models.CharField(max_length=200)
    badge = models.CharField(max_length=100, default="Core Module")
    description = models.TextField()
    icon_class = models.CharField(max_length=100, default="fas fa-cubes")
    image = models.ImageField(upload_to='ibisap/modules/', blank=True, null=True)
    static_image_path = models.CharField(max_length=255, blank=True, null=True)
    is_enterprise_ready = models.BooleanField(default=True)
    is_retail_ready = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        if self.static_image_path:
            return f"/static/{self.static_image_path}"
        return "/static/gallery/ibisap-dashboard.png"

class SiteConfiguration(models.Model):
    # Brand Identity
    brand_name = models.CharField(max_length=100, default="BHOJ RAJ")
    
    # Hero Section
    hero_badge_text = models.CharField(max_length=200, default="IT Systems Architect • Full-Stack Engineer • Poet")
    hero_greeting = models.CharField(max_length=200, default="I am Bhoj Raj Upadhayay")
    hero_title = models.CharField(max_length=200, default="Systems Architect & Creative Thinker.")
    hero_subheadline = models.TextField(default="Mastering enterprise infrastructure, Core Banking operations, SAP Business One, and Python/Django engineering — intertwined with evocative poetry and reflective literature.")
    hero_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Dynamic Stat Metrics Strip
    stat_1_number = models.CharField(max_length=50, default="5+")
    stat_1_title = models.CharField(max_length=100, default="Years Architecture")
    stat_1_sub = models.CharField(max_length=150, default="Enterprise IT & Web Systems")

    stat_2_number = models.CharField(max_length=50, default="100%")
    stat_2_title = models.CharField(max_length=100, default="NRB Compliance")
    stat_2_sub = models.CharField(max_length=150, default="Audit Trails & Disaster Recovery")

    stat_3_number = models.CharField(max_length=50, default="15+")
    stat_3_title = models.CharField(max_length=100, default="Enterprise Modules")
    stat_3_sub = models.CharField(max_length=150, default="ERP, POS, CBMS & Banking APIs")

    stat_4_number = models.CharField(max_length=50, default="50k+")
    stat_4_title = models.CharField(max_length=100, default="Lines of Code")
    stat_4_sub = models.CharField(max_length=150, default="Clean, Resilient Microservices")

    # Dynamic 4 Pillars
    pillar_1_title = models.CharField(max_length=100, default="Core Banking & CBS Systems")
    pillar_1_desc = models.TextField(default="Deep expertise in high-concurrency ledger operations, Maker-Checker RBAC authorization, and regulatory compliance under Nepal Rastra Bank guidelines.")

    pillar_2_title = models.CharField(max_length=100, default="Python & Django Architecture")
    pillar_2_desc = models.TextField(default="Crafting scalable web backends, RESTful microservices, asynchronous task queues, and resilient financial transaction pipelines.")

    pillar_3_title = models.CharField(max_length=100, default="SAP B1 & SQL HANA Ecosystem")
    pillar_3_desc = models.TextField(default="Database optimization, row-level locking consistency, and architectural design of IbiSAP — Nepal's compliant ERP alternative.")

    pillar_4_title = models.CharField(max_length=100, default="Poetic & Literary Expression")
    pillar_4_desc = models.TextField(default="Weaving evocative verses in Nepali & English, contemplating human existence, philosophy, and the quiet harmony between technology and soul.")

    # About Section
    about_me_lead = models.TextField(default="I am an IT Systems Architect, Full-Stack Engineer, and Creative Writer based in Nepal.")
    about_me_text_1 = models.TextField(default="In my professional practice, I architect and manage high-stakes Core Banking System (CBS) operations, enforce strict NRB IT security directives, design Disaster Recovery Plans (DRP), and supervise mission-critical enterprise systems.")
    about_me_text_2 = models.TextField(default="My technical foundation spans hands-on SAP Business One implementation, SQL HANA / PostgreSQL database administration, Linux server infrastructure, and full-stack Python/Django engineering.")
    about_me_text_3 = models.TextField(default="Beyond engineering determinism, I express life's reflective dimensions through poetry in Nepali and English, capturing philosophical depth and spiritual resonance.")
    
    # Contact & Links
    email_address = models.EmailField(default="bhojrajupadhayay2001@gmail.com")
    phone_number = models.CharField(max_length=100, default="+977 9848485292")
    whatsapp_number = models.CharField(max_length=100, default="+977 9848485292")
    whatsapp_url = models.URLField(default="https://wa.me/9779848485292", blank=True)
    location = models.CharField(max_length=200, default="Kathmandu / Kailali, Nepal")
    
    github_url = models.URLField(default="https://github.com/bhojrajupadhayay", blank=True)
    linkedin_url = models.URLField(default="https://linkedin.com/in/bhojrajupadhayay", blank=True)
    prakriti_prabhav_url = models.URLField(default="https://prakritiprabhav.com", blank=True)
    ibisap_live_url = models.URLField(default="https://ibisap.rajabhoj.com.np", blank=True)
    
    # Resume / CV Document
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True, help_text="Upload your PDF CV/Resume")
    resume_url = models.URLField(blank=True, help_text="External URL to CV (e.g. Google Drive, Dropbox)")

    
    footer_text = models.CharField(max_length=200, default="Bhoj Raj Upadhayay. Engineered with Precision & Soul.")

    @property
    def cv_download_url(self):
        if self.resume_file:
            return self.resume_file.url
        if self.resume_url:
            return self.resume_url
        return None

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Global Site Configuration"


