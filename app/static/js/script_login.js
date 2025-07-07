document.addEventListener('DOMContentLoaded', function() {
const logoImage = document.getElementById('logo-image');
    logoImage.onerror = function() {
        this.style.display = 'none';
        document.getElementById('logo-text').style.display = 'block';
    };
});