document.addEventListener('DOMContentLoaded', function() {
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    const indicators = document.querySelectorAll('.indicator');

    function updateIndicators() {
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === currentSlide);
        });
    }

    function showSlide(n) {
        slides.forEach(slide => slide.classList.remove('active'));
        slides[n].classList.add('active');
        updateIndicators();
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    // 按钮事件监听
    document.querySelector('.next-btn').addEventListener('click', () => {
        nextSlide();
        resetInterval();
    });

    document.querySelector('.prev-btn').addEventListener('click', () => {
        prevSlide();
        resetInterval();
    });

    // 指示器点击事件
    indicators.forEach(indicator => {
        indicator.addEventListener('click', () => {
            currentSlide = parseInt(indicator.dataset.slide);
            showSlide(currentSlide);
            resetInterval();
        });
    });

    // 自动播放逻辑
    let slideInterval = setInterval(nextSlide, 5000);

    function resetInterval() {
        clearInterval(slideInterval);
        slideInterval = setInterval(nextSlide, 5000);
    }
});