// Test JavaScript file for preview linking
document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript loaded successfully!');
    
    const testBtn = document.getElementById('testBtn');
    const output = document.getElementById('output');
    let clickCount = 0;
    
    if (testBtn && output) {
        testBtn.addEventListener('click', function() {
            clickCount++;
            
            const messages = [
                '🎉 JavaScript is working!',
                '✨ CSS and JS are properly linked!',
                '🚀 Preview system is functioning!',
                '💫 All files connected successfully!',
                '🎯 Perfect! Everything works!'
            ];
            
            const randomMessage = messages[Math.floor(Math.random() * messages.length)];
            output.textContent = `${randomMessage} (Click #${clickCount})`;
            output.style.color = getRandomColor();
            
            // Add some visual feedback
            testBtn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                testBtn.style.transform = 'scale(1)';
            }, 150);
        });
    }
    
    // Add some dynamic styling
    function getRandomColor() {
        const colors = ['#667eea', '#764ba2', '#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3'];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    // Animate the color box
    const colorBox = document.querySelector('.color-box');
    if (colorBox) {
        setInterval(() => {
            const hue = Math.floor(Math.random() * 360);
            colorBox.style.background = `linear-gradient(45deg, hsl(${hue}, 70%, 60%), hsl(${hue + 60}, 70%, 60%))`;
        }, 3000);
    }
    
    // Add welcome message
    setTimeout(() => {
        console.log('🎯 Test complete: HTML, CSS, and JavaScript are all properly linked!');
    }, 1000);
});
