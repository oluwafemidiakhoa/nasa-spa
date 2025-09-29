/**
 * Advanced Animation Controller for NASA Space Weather System
 * Provides smooth transitions, loading effects, and performance optimizations
 */

class NASAAnimationController {
    constructor() {
        this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.loadingElement = null;
        this.activeAnimations = new Set();
        this.performanceMode = this.detectPerformanceMode();
        
        this.init();
    }

    init() {
        this.createLoadingScreen();
        this.setupPageTransitions();
        this.setupCardAnimations();
        this.setupRippleEffects();
        this.optimizeForPerformance();
        
        console.log('🎬 NASA Animation Controller initialized');
    }

    detectPerformanceMode() {
        // Detect device performance capabilities
        const memory = navigator.deviceMemory || 4;
        const cores = navigator.hardwareConcurrency || 4;
        const connection = navigator.connection?.effectiveType || '4g';
        
        if (memory >= 8 && cores >= 8 && connection === '4g') return 'high';
        if (memory >= 4 && cores >= 4) return 'medium';
        return 'low';
    }

    createLoadingScreen() {
        this.loadingElement = document.createElement('div');
        this.loadingElement.className = 'nasa-loading-spinner gpu-accelerated';
        this.loadingElement.innerHTML = `
            <div class="orbital-loader">
                <div class="orbit"></div>
                <div class="orbit"></div>
                <div class="orbit"></div>
                <div class="sun-core"></div>
            </div>
            <div class="loading-text">NASA SPACE WEATHER SYSTEM</div>
            <div class="loading-progress" id="loading-progress">Initializing mission control...</div>
        `;
        
        document.body.appendChild(this.loadingElement);
    }

    updateLoadingProgress(message, percentage = null) {
        const progressElement = document.getElementById('loading-progress');
        if (progressElement) {
            let displayMessage = message;
            if (percentage !== null) {
                displayMessage += ` (${percentage}%)`;
            }
            progressElement.textContent = displayMessage;
        }
    }

    hideLoadingScreen(delay = 1000) {
        setTimeout(() => {
            if (this.loadingElement) {
                this.loadingElement.classList.add('hidden');
                setTimeout(() => {
                    if (this.loadingElement && this.loadingElement.parentNode) {
                        this.loadingElement.parentNode.removeChild(this.loadingElement);
                    }
                }, 800);
            }
        }, delay);
    }

    setupPageTransitions() {
        // Create page transition overlay
        const transitionOverlay = document.createElement('div');
        transitionOverlay.className = 'page-transition';
        transitionOverlay.innerHTML = `
            <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh;">
                <div class="orbital-loader">
                    <div class="orbit"></div>
                    <div class="orbit"></div>
                    <div class="sun-core"></div>
                </div>
                <div style="color: #00ffff; font-family: 'JetBrains Mono', monospace; margin-top: 20px;">
                    Transitioning to mission module...
                </div>
            </div>
        `;
        document.body.appendChild(transitionOverlay);

        // Intercept navigation for smooth transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]:not([target="_blank"]):not([href^="#"])');
            if (link && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                this.transitionToPage(link.href);
            }
        });
    }

    transitionToPage(url) {
        const overlay = document.querySelector('.page-transition');
        overlay.classList.add('active');
        
        setTimeout(() => {
            window.location.href = url;
        }, 400);
    }

    setupCardAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '50px'
        };

        const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                    }, index * 100); // Stagger the animations
                }
            });
        }, observerOptions);

        // Observe dashboard cards
        setTimeout(() => {
            const cards = document.querySelectorAll('.dashboard-card, .system-card, .data-card');
            cards.forEach((card, index) => {
                card.classList.add('card-entrance');
                cardObserver.observe(card);
            });
        }, 100);
    }

    setupRippleEffects() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.launch-btn, .control-button, .ripple-button');
            if (button && !this.isReducedMotion) {
                this.createRipple(button, e);
            }
        });
    }

    createRipple(element, event) {
        const rect = element.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const ripple = document.createElement('div');
        ripple.style.position = 'absolute';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.width = '0';
        ripple.style.height = '0';
        ripple.style.background = 'rgba(255, 255, 255, 0.3)';
        ripple.style.borderRadius = '50%';
        ripple.style.transform = 'translate(-50%, -50%)';
        ripple.style.animation = 'ripple-expand 0.6s ease-out';
        ripple.style.pointerEvents = 'none';

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    animateCounterUp(element, target, duration = 2000) {
        if (this.isReducedMotion) {
            element.textContent = target;
            return;
        }

        const start = parseInt(element.textContent) || 0;
        const range = target - start;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (range * easeOut));
            
            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    animateProgressBar(element, percentage, duration = 1500) {
        if (this.isReducedMotion) {
            element.style.width = percentage + '%';
            return;
        }

        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeOut = 1 - Math.pow(1 - progress, 2);
            const currentWidth = percentage * easeOut;
            
            element.style.width = currentWidth + '%';

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    createFloatingParticles(container, count = 20) {
        if (this.isReducedMotion || this.performanceMode === 'low') return;

        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = Math.random() * 3 + 1 + 'px';
            particle.style.height = particle.style.width;
            particle.style.background = `rgba(0, ${Math.floor(Math.random() * 255)}, 255, 0.6)`;
            particle.style.borderRadius = '50%';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `float3d ${Math.random() * 10 + 5}s ease-in-out infinite`;
            particle.style.animationDelay = Math.random() * 5 + 's';
            particle.style.pointerEvents = 'none';
            particle.style.zIndex = '-1';
            
            container.appendChild(particle);
        }
    }

    addGlowEffect(element, color = '0, 255, 255') {
        if (this.isReducedMotion) return;

        element.style.transition = 'all 0.3s ease';
        element.addEventListener('mouseenter', () => {
            element.style.boxShadow = `0 0 20px rgba(${color}, 0.6), 0 0 40px rgba(${color}, 0.3)`;
        });
        
        element.addEventListener('mouseleave', () => {
            element.style.boxShadow = '';
        });
    }

    optimizeForPerformance() {
        // Add GPU acceleration to key elements
        const keyElements = document.querySelectorAll(
            '.dashboard-card, .system-card, .hud-panel, .panel'
        );
        
        keyElements.forEach(element => {
            element.classList.add('gpu-accelerated');
        });

        // Reduce animations on low-performance devices
        if (this.performanceMode === 'low') {
            document.documentElement.style.setProperty('--animation-speed-fast', '0.1s');
            document.documentElement.style.setProperty('--animation-speed-normal', '0.2s');
            document.documentElement.style.setProperty('--animation-speed-slow', '0.3s');
        }
    }

    showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification-slide notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, rgba(0, 40, 80, 0.95), rgba(0, 20, 40, 0.9));
            border: 2px solid ${type === 'success' ? '#00ff00' : type === 'error' ? '#ff0000' : '#00ffff'};
            border-radius: 10px;
            padding: 15px 20px;
            color: white;
            font-family: 'Inter', sans-serif;
            max-width: 300px;
            backdrop-filter: blur(10px);
            z-index: 10000;
            cursor: pointer;
        `;
        
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 5px;">${type.toUpperCase()}</div>
            <div>${message}</div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Auto-remove
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 600);
        }, duration);

        // Click to dismiss
        notification.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 600);
        });
    }

    addDataStreamEffect(element) {
        if (this.isReducedMotion) return;
        
        element.classList.add('data-stream');
        
        const streamInterval = setInterval(() => {
            if (!document.contains(element)) {
                clearInterval(streamInterval);
                return;
            }
            
            // Add brief glow effect to simulate data updates
            element.style.transition = 'box-shadow 0.3s ease';
            element.style.boxShadow = '0 0 15px rgba(0, 255, 0, 0.4)';
            
            setTimeout(() => {
                element.style.boxShadow = '';
            }, 300);
            
        }, Math.random() * 5000 + 3000); // Random intervals between 3-8 seconds
    }

    destroy() {
        // Clean up animations and observers
        this.activeAnimations.forEach(animation => {
            if (animation.cancel) animation.cancel();
        });
        this.activeAnimations.clear();
        
        if (this.loadingElement && this.loadingElement.parentNode) {
            this.loadingElement.parentNode.removeChild(this.loadingElement);
        }
    }
}

// CSS for ripple effect
const rippleCSS = `
@keyframes ripple-expand {
    to {
        width: 300px;
        height: 300px;
        opacity: 0;
    }
}
`;

// Add the CSS to the document
const style = document.createElement('style');
style.textContent = rippleCSS;
document.head.appendChild(style);

// Initialize animation controller when DOM is ready
let nasaAnimationController;

document.addEventListener('DOMContentLoaded', () => {
    nasaAnimationController = new NASAAnimationController();
});

// Export for use in other scripts
window.NASAAnimationController = NASAAnimationController;