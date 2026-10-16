const API_BASE = '';

function createIcon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'icon');
    svg.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', `#${name}`);
    svg.append(use);
    return svg;
}

function safeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    try {
        const url = new URL(value, window.location.origin);
        return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
    } catch (_) {
        return '';
    }
}

async function loadProjects() {
    const container = document.getElementById('projects-container');
    const toggle = document.getElementById('projects-toggle');
    toggle.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    try {
        const response = await fetch(`${API_BASE}/api/projects`);
        if (!response.ok) throw new Error('Project request failed');
        const projects = await response.json();
        if (!Array.isArray(projects)) throw new Error('Invalid projects');
        container.replaceChildren();
        document.getElementById('project-count').textContent = `${String(projects.length).padStart(2, '0')} 个实际项目`;
        if (!projects.length) {
            const empty = document.createElement('p');
            empty.className = 'load-state';
            empty.textContent = '项目案例正在整理中，欢迎直接沟通你的需求。';
            container.append(empty);
            return;
        }
        projects.forEach((project, index) => {
            const card = document.createElement('article');
            card.className = 'project-card';
            card.hidden = index >= 3;
            const href = safeUrl(project.project_url);
            const preview = document.createElement(href ? 'a' : 'div');
            preview.className = 'project-image';
            if (href) {
                preview.href = href;
                preview.target = '_blank';
                preview.rel = 'noopener noreferrer';
                preview.setAttribute('aria-label', `访问${project.title}（新窗口）`);
            }
            const src = safeUrl(project.image_url);
            if (src) {
                const image = document.createElement('img');
                image.src = src;
                image.alt = project.title || '项目预览';
                image.loading = 'lazy';
                image.addEventListener('error', () => {
                    image.remove();
                    const fallback = document.createElement('span');
                    fallback.className = 'load-state';
                    fallback.textContent = project.title || '项目案例';
                    preview.prepend(fallback);
                }, {once: true});
                preview.append(image);
            }
            if (href) {
                const visit = document.createElement('span');
                visit.className = 'project-visit';
                visit.append(createIcon('i-diagonal'));
                preview.append(visit);
            }
            const meta = document.createElement('div');
            meta.className = 'project-meta';
            const title = document.createElement('h3');
            title.textContent = project.title || '项目';
            const category = document.createElement('span');
            category.className = 'project-category';
            category.textContent = project.category || '软件开发';
            meta.append(title, category);
            const description = document.createElement('p');
            description.textContent = project.description || '';
            card.append(preview, meta, description);
            container.append(card);
        });
        if (projects.length > 3) {
            toggle.hidden = false;
            toggle.textContent = `查看全部 ${projects.length} 个项目 +`;
            toggle.onclick = () => {
                const expanded = toggle.getAttribute('aria-expanded') !== 'true';
                container.querySelectorAll('.project-card').forEach((card, index) => {
                    card.hidden = !expanded && index >= 3;
                });
                toggle.setAttribute('aria-expanded', String(expanded));
                toggle.textContent = expanded ? '收起更多项目 −' : `查看全部 ${projects.length} 个项目 +`;
            };
        }
    } catch (_) {
        const error = document.createElement('p');
        error.className = 'load-state';
        error.textContent = '项目暂时未能加载。';
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.textContent = '重新加载';
        retry.addEventListener('click', loadProjects);
        error.append(retry);
        container.replaceChildren(error);
        document.getElementById('project-count').textContent = '项目案例';
    }
}

async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE}/api/skills`);
        if (!response.ok) return;
        const skills = await response.json();
        if (!Array.isArray(skills)) return;
        const container = document.getElementById('skills-container');
        container.replaceChildren();
        skills.forEach(skill => {
            if (!skill.name) return;
            const tag = document.createElement('span');
            tag.textContent = skill.name;
            container.append(tag);
        });
    } catch (_) {
        // Service descriptions remain usable when optional skill data is unavailable.
    }
}

function initNavigation() {
    const menu = document.querySelector('.menu-toggle');
    const links = document.getElementById('nav-links');
    const closeMenu = () => {
        links.classList.remove('is-open');
        menu.setAttribute('aria-expanded', 'false');
        menu.setAttribute('aria-label', '展开导航');
    };
    menu.addEventListener('click', () => {
        const open = menu.getAttribute('aria-expanded') !== 'true';
        menu.setAttribute('aria-expanded', String(open));
        menu.setAttribute('aria-label', open ? '收起导航' : '展开导航');
        links.classList.toggle('is-open', open);
    });
    links.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
            closeMenu();
            menu.focus();
        }
    });
    document.querySelectorAll('[data-service]').forEach(link => link.addEventListener('click', () => {
        document.getElementById('request-type').value = link.dataset.service;
    }));
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            document.querySelectorAll('[data-nav-link]').forEach(link => {
                const active = link.hash === `#${entry.target.id}`;
                link.classList.toggle('active', active);
                if (active) link.setAttribute('aria-current', 'location');
                else link.removeAttribute('aria-current');
            });
        });
    }, {rootMargin: '-15% 0px -65% 0px'});
    document.querySelectorAll('main>section[id]').forEach(section => observer.observe(section));
}

    function initContactForm() {
        const form = document.getElementById('contact-form');
        const contactType = document.getElementById('contact-type');
        const contactValue = document.getElementById('contact-value');
        const button = document.getElementById('contact-submit');
        const status = document.getElementById('contact-status');
        const submitLabel = button.innerHTML;
        const updateContactType = () => {
            const options = {
                email: ['邮箱地址 *', 'email', 'email', '方便回复你的邮箱'],
                wechat: ['微信号 *', 'text', 'off', '方便联系你的微信号'],
                phone: ['电话号码 *', 'tel', 'tel', '方便联系你的电话号码'],
            };
            const [label, type, autocomplete, placeholder] = options[contactType.value];
            document.getElementById('contact-value-label').textContent = label;
            contactValue.type = type;
            contactValue.autocomplete = autocomplete;
            contactValue.placeholder = placeholder;
        };
        contactType.addEventListener('change', updateContactType);
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (button.disabled || !form.reportValidity()) return;
            const data = Object.fromEntries(new FormData(form));
            for (const field of ['name', 'contact', 'content']) data[field] = data[field].trim();
            if (!data.name || !data.contact || !data.content) {
                status.dataset.state = 'error';
                status.textContent = '请填写所有必填字段，不能只输入空格。';
                return;
            }
            const service = document.getElementById('request-type').value;
            if (service) data.content = `[需求类型：${service}]\n${data.content}`;
            button.disabled = true;
            button.textContent = '正在提交…';
            status.dataset.state = '';
            status.textContent = '正在提交你的私密留言，请稍候。';
            try {
                const response = await fetch(`${API_BASE}/api/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || '提交失败，请稍后重试。');
                form.reset();
                updateContactType();
                status.dataset.state = 'success';
                status.textContent = result.message;
            } catch (error) {
                status.dataset.state = 'error';
                status.textContent = error instanceof TypeError || error instanceof SyntaxError
                    ? '暂时无法提交，请检查网络后重试。你填写的内容已保留。'
                    : error.message;
            } finally {
                button.disabled = false;
                button.innerHTML = submitLabel;
            }
        });
    }


document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initContactForm();
    loadProjects();
    loadSkills();
});
