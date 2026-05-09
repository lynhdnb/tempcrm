// JavaScript для работы выпадающего меню в админке
(function() {
    'use strict';
    
    // Закрытие меню при клике вне его
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.action-menu')) {
            document.querySelectorAll('.action-menu.active').forEach(function(menu) {
                menu.classList.remove('active');
            });
        }
    });
    
    // Открытие/закрытие меню по клику на кнопку
    document.querySelectorAll('.action-menu-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            var menu = this.closest('.action-menu');
            
            // Закрываем все другие открытые меню
            document.querySelectorAll('.action-menu.active').forEach(function(m) {
                if (m !== menu) {
                    m.classList.remove('active');
                }
            });
            
            // Переключаем текущее меню
            menu.classList.toggle('active');
        });
    });
})();