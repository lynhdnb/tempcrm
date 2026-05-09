/**
 * Скрипты для страницы списка клиентов
 * - Обработка клика по строке таблицы
 * - Управление выпадающим меню действий
 */

document.addEventListener('DOMContentLoaded', function() {
    // Обработка клика по строке таблицы
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', function(e) {
            // Если клик не по кнопке меню и не по ссылке
            if (!e.target.closest('.action-menu') && !e.target.closest('a')) {
                const href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            }
        });
    });
    
    // Управление выпадающим меню
    document.querySelectorAll('.action-menu-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const menu = this.closest('.action-menu');
            
            // Закрываем все открытые меню
            document.querySelectorAll('.action-menu.active').forEach(m => {
                if (m !== menu) m.classList.remove('active');
            });
            
            // Переключаем текущее меню
            menu.classList.toggle('active');
        });
    });
    
    // Закрываем меню при клике вне его
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.action-menu')) {
            document.querySelectorAll('.action-menu.active').forEach(m => {
                m.classList.remove('active');
            });
        }
    });
});