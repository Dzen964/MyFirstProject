// Theme Switcher
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply theme on page load
    applyTheme(currentTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            applyTheme(newTheme);
            
            // Save theme preference through AJAX
            updateUserThemePreference(newTheme);
        });
    }
    
    function applyTheme(theme) {
        // Update the document class
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            
            // Update theme toggle icon
            if (themeToggle) {
                themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
                themeToggle.setAttribute('title', 'Switch to Light Mode');
            }
        } else {
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
            
            // Update theme toggle icon
            if (themeToggle) {
                themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
                themeToggle.setAttribute('title', 'Switch to Dark Mode');
            }
        }
        
        // Update link to theme CSS file
        let themeLink = document.getElementById('theme-css');
        if (!themeLink) {
            themeLink = document.createElement('link');
            themeLink.id = 'theme-css';
            themeLink.rel = 'stylesheet';
            document.head.appendChild(themeLink);
        }
        themeLink.href = `/static/css/${theme}.css`;
        
        // Store theme preference in local storage
        localStorage.setItem('theme', theme);
    }
    
    function updateUserThemePreference(theme) {
        // Update user's theme preference if logged in
        fetch('/auth/update_theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ theme: theme })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Theme preference updated:', data);
        })
        .catch(error => {
            console.error('Error updating theme preference:', error);
        });
    }
    
    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
});
