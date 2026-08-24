// Private Portal Dashboard Logic
document.addEventListener("DOMContentLoaded", function() {
    // 1. Dynamic Greeting
    const hour = new Date().getHours();
    let greeting = "Welcome back";
    if (hour >= 5 && hour < 12) greeting = "Good morning";
    else if (hour >= 12 && hour < 17) greeting = "Good afternoon";
    else if (hour >= 17 && hour < 22) greeting = "Good evening";
    else greeting = "Late night thoughts";
    
    const greetingEl = document.getElementById("dynamic-greeting");
    if (greetingEl) {
        // Need to pass the username from DOM as we don't have django templating in JS
        const currentName = greetingEl.dataset.username || "Creator";
        greetingEl.textContent = `${greeting}, ${currentName}`;
    }

    // 2. Feed Filtering
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.memory-card[data-type]');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            
            cards.forEach(card => {
                const type = card.getAttribute('data-type');
                if (filter === 'all' || type === filter || (filter === 'blog' && type === 'novel')) {
                    card.style.display = 'block';
                    card.style.opacity = '1';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // 3. Floating Action Button Logic
    const fabMain = document.getElementById('fab-main');
    const fabContainer = document.getElementById('fab-container');
    
    if (fabMain) {
        fabMain.addEventListener('click', () => {
            fabContainer.classList.toggle('active');
            const icon = fabMain.querySelector('i');
            if (fabContainer.classList.contains('active')) {
                icon.classList.replace('fa-plus', 'fa-times');
            } else {
                icon.classList.replace('fa-times', 'fa-plus');
            }
        });
    }

    // 4. Social Actions logic
    window.toggleSocial = function(btn, url, csrfToken, successCallback) {
        const formData = new FormData();
        formData.append('content_type_id', btn.dataset.ct);
        formData.append('object_id', btn.dataset.id);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(url, { method: 'POST', body: formData, headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(r => r.json()).then(data => { if(data.status==='ok') successCallback(data, btn); });
    }

    window.toggleReflections = function(btn) {
        const card = btn.closest('.memory-card');
        const section = card.querySelector('.comments-section');
        section.style.display = section.style.display === 'none' ? 'block' : 'none';
        if (section.style.display === 'block') section.querySelector('input').focus();
    };

    window.shareMemory = function(id, type, baseUrl) {
        const url = baseUrl + "?q=" + id;
        navigator.clipboard.writeText(url).then(() => {
            // Premium toast notification
            const toast = document.createElement('div');
            toast.innerHTML = '<i class="fas fa-link" style="margin-right:0.5rem;"></i> Memory link copied to clipboard';
            toast.style.cssText = 'position:fixed;bottom:2rem;left:50%;transform:translateX(-50%) translateY(20px);background:linear-gradient(135deg,#00d2ff,#9d50bb);color:#fff;padding:1rem 2rem;border-radius:30px;font-weight:600;font-size:0.95rem;z-index:9999;box-shadow:0 10px 40px rgba(0,210,255,0.4);opacity:0;transition:all 0.4s cubic-bezier(0.4,0,0.2,1);display:flex;align-items:center;';
            document.body.appendChild(toast);
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateX(-50%) translateY(0)';
            });
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(-50%) translateY(20px)';
                setTimeout(() => toast.remove(), 400);
            }, 3000);
        });
    };

    // 5. Zen Mode Expert Logic
    const quotes = [
        "The present moment is the only moment available to us.",
        "Your digital sanctuary is a reflection of your inner peace.",
        "In the stillness, you find yourself.",
        "Focus on the breath, let the pixels fade.",
        "Everything you need is already within you.",
        "Peace comes from within. Do not seek it without.",
        "Deep focus is the highest form of respect for your soul."
    ];

    const zenBtn = document.createElement('button');
    zenBtn.innerHTML = '<i class="fas fa-eye"></i>';
    zenBtn.className = 'zen-toggle';
    zenBtn.style = 'position: fixed; bottom: 7rem; right: 2rem; width: 60px; height: 60px; border-radius: 50%; background: var(--accent-blue); border: none; color: #fff; font-size: 1.5rem; cursor: pointer; z-index: 2000; box-shadow: 0 5px 20px rgba(0,210,255,0.4); transition: all 0.3s ease;';
    document.body.appendChild(zenBtn);

    window.toggleZenExpert = function() {
        const overlay = document.getElementById('zen-overlay');
        const quoteContainer = document.getElementById('zen-quote-container');
        
        if (overlay.classList.contains('active')) {
            overlay.classList.remove('active');
            setTimeout(() => { overlay.style.display = 'none'; }, 800);
            zenBtn.style.background = 'var(--accent-blue)';
            zenBtn.innerHTML = '<i class="fas fa-eye"></i>';
        } else {
            overlay.style.display = 'flex';
            quoteContainer.innerText = `"${quotes[Math.floor(Math.random() * quotes.length)]}"`;
            setTimeout(() => { overlay.classList.add('active'); }, 10);
            zenBtn.style.background = '#8b5cf6';
            zenBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            
            // Cycle quotes
            const quoteInterval = setInterval(() => {
                if (!overlay.classList.contains('active')) {
                    clearInterval(quoteInterval);
                    return;
                }
                quoteContainer.style.opacity = '0';
                setTimeout(() => {
                    quoteContainer.innerText = `"${quotes[Math.floor(Math.random() * quotes.length)]}"`;
                    quoteContainer.style.opacity = '0.8';
                }, 1000);
            }, 10000);
        }
    };

    zenBtn.addEventListener('click', toggleZenExpert);

    // Close FAB when clicking outside
    document.addEventListener('click', (e) => {
        if (fabContainer && !fabContainer.contains(e.target) && fabContainer.classList.contains('active')) {
            fabContainer.classList.remove('active');
            if(fabMain && fabMain.querySelector('i')){
                fabMain.querySelector('i').classList.replace('fa-times', 'fa-plus');
            }
        }
    });
});
