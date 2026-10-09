(function() {
    const scripts = [
        '/static/js/utils/toast.js',
        '/static/js/utils/loading.js',
        '/static/js/utils/header.js',
        '/static/js/utils/security.js',
        '/static/js/utils/admin_ui.js'
    ];
    
    scripts.forEach(src => {
        const script = document.createElement('script');
        script.src = src;
        script.async = false; // Execute in order
        document.head.appendChild(script);
    });
})();