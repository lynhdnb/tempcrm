from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class CourseCategory(models.Model):
    """Категории курсов"""
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Слаг", unique=True)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField("Иконка", max_length=20, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Категория курса"
        verbose_name_plural = "Категории курсов"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """Курсы обучения"""
    DURATION_CHOICES = [
        ('1_month', '1 месяц'),
        ('3_months', '3 месяца'),
        ('6_months', '6 месяцев'),
        ('9_months', '9 месяцев'),
        ('1_year', '1 год'),
        ('open', 'Открытая длительность (по желанию)'),
    ]

    # Типы занятий
    LESSON_TYPE_CHOICES = [
        ('STANDARD', 'Обычное занятие с преподавателем'),
        ('PRACTICE', 'Самостоятельная практика без преподавателя'),
    ]

    name = models.CharField("Название курса", max_length=200, help_text="Краткое название курса, например: DJ Basics, Продвинутый миксинг")
    slug = models.SlugField("Слаг", unique=True, help_text="URL-адрес курса на латинице, например: dj-basics")
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Категория",
        help_text="Раздел, к которому относится курс (например: DJ-инг, Звукозапись, Мастер-классы)"
    )
    
    description = models.TextField("Краткое описание", blank=True, help_text="Краткое описание курса для списка (1-2 предложения)")
    full_description = models.TextField("Полное описание", blank=True, help_text="Подробное описание для договора и прайс-листа")
    
    duration = models.CharField(
        "Длительность курса",
        max_length=20,
        choices=DURATION_CHOICES,
        default='3_months',
        help_text="Рекомендуемая длительность прохождения курса"
    )
    
    # Программа и структура
    total_lessons = models.PositiveIntegerField(
        "Всего занятий в курсе",
        default=12,
        help_text="Общее количество занятий (включая самостоятельную практику). Например: 8 занятий с преподом + 4 самостоятельных = 12"
    )
    curriculum = models.TextField(
        "Программа курса",
        blank=True,
        help_text="Перечень тем/модулей через запятую или список. Что будет изучать студент"
    )
    lesson_duration = models.PositiveIntegerField(
        "Длительность занятия (минут)",
        default=60,
        help_text="Стандартная длительность одного занятия в минутах (45, 60, 90)"
    )

    # Цены - для гибкости ценообразования
    base_price = models.DecimalField(
        "Базовая цена курса (руб)",
        max_digits=10,
        decimal_places=2,
        help_text="Полная стоимость курса для договора и прайс-листа (без скидок)"
    )
    promo_price = models.DecimalField(
        "Акционная цена (руб)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Фактическая цена к оплате (со скидкой). Если не указано, используется базовая цена"
    )
    
    # Статусы
    is_active = models.BooleanField("Активен", default=True, help_text="Курс доступен для записи")
    is_popular = models.BooleanField("Популярный", default=False, help_text="Показывать в разделе популярных курсов")
    
    # Материалы
    materials_url = models.URLField("Ссылка на материалы", blank=True, help_text="Google Drive, Dropbox или другая ссылка на учебные материалы")
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['-is_popular', 'name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def active_enrollments_count(self):
        """Количество активных записей на курс"""
        return self.enrollments.filter(status='ACTIVE').count()
    
    @property
    def available_slots(self):
        """Количество активных записей на курс (без ограничения max_students)"""
        return self.active_enrollments_count
    
    @property
    def actual_price(self):
        """Фактическая цена к оплате (акционная или базовая)"""
        return self.promo_price if self.promo_price else self.base_price


class Enrollment(models.Model):
    """Запись студента на курс"""
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает подтверждения'),
        ('ACTIVE', 'Активен'),
        ('COMPLETED', 'Завершен'),
        ('DROPPED', 'Брошен'),
        ('PAUSED', 'Приостановлен'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('NOT_PAID', 'Не оплачено'),
        ('PARTIAL', 'Частично оплачено'),
        ('PAID', 'Оплачено'),
    ]

    INSTALLMENT_CHOICES = [
        ('NONE', 'Разовый платёж'),
        ('BANK_2', 'Банковская рассрочка 2 платежа'),
        ('BANK_3', 'Банковская рассрочка 3 платежа'),
        ('BANK_6', 'Банковская рассрочка 6 платежей'),
        ('SCHOOL_2', 'Рассрочка школы 2 платежа'),
        ('SCHOOL_3', 'Рассрочка школы 3 платежа'),
        ('SCHOOL_6', 'Рассрочка школы 6 платежей'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Курс"
    )
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Студент"
    )

    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField("Статус оплаты", max_length=20, choices=PAYMENT_STATUS_CHOICES, default='NOT_PAID')
    
    # Даты
    start_date = models.DateField("Дата начала")
    
    # Гибкость при продаже (можно менять для лояльности)
    total_lessons = models.PositiveIntegerField("Всего занятий в курсе", default=10)
    total_practice_hours = models.PositiveIntegerField("Часов практики", default=30, help_text="0 для безлимита")
    is_unlimited_practice = models.BooleanField("Безлимитная практика", default=False)
    
    # Прогресс
    completed_lessons = models.PositiveIntegerField("Отработано с преподавателем", default=0)
    completed_practice_minutes = models.PositiveIntegerField("Отработано практики (минуты)", default=0)
    
    # Рассрочка
    installment_type = models.CharField("Тип рассрочки", max_length=20, choices=INSTALLMENT_CHOICES, default='NONE')
    installment_bank_fee_percent = models.DecimalField("Комиссия банка (%)", max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Оплата
    enrolled_price = models.DecimalField(
        "Цена при записи (руб)",
        max_digits=10,
        decimal_places=2,
        help_text="Цена, по которой записался студент (может отличаться от базовой)"
    )
    paid_amount = models.DecimalField("Оплачено (руб)", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Преподаватель (студент может ходить к разным)
    assigned_teacher = models.ForeignKey(
        'EmployeeProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments',
        verbose_name="Назначенный преподаватель"
    )
    
    # Заметки
    notes = models.TextField("Заметки", blank=True)
    source = models.CharField(
        "Источник записи",
        max_length=100,
        blank=True,
        help_text="Откуда записался: сайт, телефон, рекомендация"
    )
    
    # Кто записал
    enrolled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_enrollments',
        verbose_name="Записал"
    )
    
    created_at = models.DateTimeField("Дата записи", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курсы"
        ordering = ['-created_at']
        unique_together = ['course', 'client', 'start_date']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['course', 'status']),
        ]

    def __str__(self):
        return f"{self.client} → {self.course} ({self.get_status_display()})"
    
    # Properties
    @property
    def remaining_lessons(self):
        """Оставшиеся занятия с преподавателем"""
        return max(0, self.total_lessons - self.completed_lessons)
    
    @property
    def remaining_practice_hours(self):
        """Оставшиеся часы практики"""
        if self.is_unlimited_practice:
            return float('inf')
        return max(0, (self.total_practice_hours * 60 - self.completed_practice_minutes) // 60)
    
    @property
    def completed_practice_hours(self):
        """Отработанные часы практики"""
        return self.completed_practice_minutes // 60
    
    @property
    def progress_percentage(self):
        """Процент прохождения курса"""
        total_lessons = self.total_lessons
        total_practice_hours = self.total_practice_hours if not self.is_unlimited_practice else 0
        
        if total_lessons == 0 and total_practice_hours == 0:
            return 0
        
        lessons_progress = (self.completed_lessons / total_lessons * 100) if total_lessons > 0 else 100
        practice_progress = (self.completed_practice_minutes / (total_practice_hours * 60) * 100) if total_practice_hours > 0 else 100
        
        return int((lessons_progress + practice_progress) / 2)
    
    @property
    def is_completed(self):
        """Завершен ли курс"""
        lessons_done = self.completed_lessons >= self.total_lessons
        if self.is_unlimited_practice:
            return lessons_done
        practice_done = self.completed_practice_minutes >= (self.total_practice_hours * 60)
        return lessons_done and practice_done
    
    def update_progress(self):
        """Пересчитать прогресс на основе занятий"""
        from lessons.models import Lesson
        
        self.completed_lessons = self.lessons.filter(
            lesson_type='STANDARD',
            status='completed'
        ).count()
        
        practice_minutes = self.lessons.filter(
            lesson_type='PRACTICE',
            status='completed'
        ).aggregate(total=models.Sum('duration_minutes'))['total'] or 0
        self.completed_practice_minutes = practice_minutes
        
        self.save(update_fields=['completed_lessons', 'completed_practice_minutes'])
    
    @property
    def remaining_amount(self):
        """Оставшаяся сумма к оплате"""
        return self.enrolled_price - self.paid_amount


class Role(models.Model):
    """Роли пользователей"""
    ROLE_CHOICES = [
        ('OWNER', 'Владелец'),
        ('ADMIN', 'Администратор'),
        ('MANAGER', 'Менеджер'),
        ('TEACHER', 'Преподаватель'),
        ('STUDENT', 'Ученик'),
    ]

    code = models.CharField("Код роли", max_length=20, unique=True, choices=ROLE_CHOICES)
    name = models.CharField("Название", max_length=50)
    description = models.TextField("Описание", blank=True)
    
    # Права по умолчанию
    can_view_clients = models.BooleanField("Просмотр клиентов", default=False)
    can_edit_clients = models.BooleanField("Редактирование клиентов", default=False)
    can_view_finance = models.BooleanField("Просмотр финансов", default=False)
    can_edit_finance = models.BooleanField("Редактирование финансов", default=False)
    can_view_schedule = models.BooleanField("Просмотр расписания", default=False)
    can_edit_schedule = models.BooleanField("Редактирование расписания", default=False)
    can_view_tasks = models.BooleanField("Просмотр задач", default=False)
    can_create_tasks = models.BooleanField("Создание задач", default=False)
    can_manage_users = models.BooleanField("Управление пользователями", default=False)
    can_view_reports = models.BooleanField("Просмотр отчетов", default=False)
    can_manage_settings = models.BooleanField("Настройки системы", default=False)
    
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.get_code_display()})"


class RoleAssignment(models.Model):
    """Назначение ролей пользователям"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='assignments')
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles',
        editable=False
    )
    is_primary = models.BooleanField("Основная роль", default=False)
    expires_at = models.DateField("Истекает", null=True, blank=True)
    
    created_at = models.DateTimeField("Дата назначения", auto_now_add=True)

    class Meta:
        verbose_name = "Назначение роли"
        verbose_name_plural = "Назначения ролей"
        unique_together = ['user', 'role']
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class Client(models.Model):
    """Модель клиента (ученика)"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Активный'),
        ('SILENT', 'Молчун (>14 дней)'),
        ('LOST', 'Потеряшка (>30 дней)'),
        ('CANCELLED', 'Расторгнул'),
        ('POTENTIAL', 'Потенциальный'),
    ]

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    # Основная информация
    first_name = models.CharField("Имя", max_length=50)
    last_name = models.CharField("Фамилия", max_length=50)
    middle_name = models.CharField("Отчество", max_length=50, blank=True)
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)

    # Контакты
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True)
    address = models.TextField("Адрес", blank=True)

    # Родитель (для несовершеннолетних)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родитель"
    )

    # Статусы
    status = models.CharField(
        "Статус клиента",
        max_length=20,
        choices=STATUS_CHOICES,
        default='POTENTIAL',
        help_text="Автообновляется на основе взаимодействий"
    )
    
    last_interaction_date = models.DateField(
        "Дата последнего взаимодействия",
        null=True,
        blank=True,
        editable=False,
        help_text="Автообновляется при создании взаимодействия"
    )
    
    silent_days = models.PositiveIntegerField(
        "Дней без активности",
        default=0,
        editable=False,
        help_text="Сколько дней прошло с последнего взаимодействия"
    )

    # Дополнительные поля
    source = models.CharField(
        "Источник",
        max_length=50,
        blank=True,
        help_text="Откуда пришел: рекомендация, реклама, сайт и т.д."
    )
    
    notes = models.TextField("Заметки о клиенте", blank=True)
    tags = models.CharField(
        "Теги",
        max_length=200,
        blank=True,
        help_text="Теги через запятую: фортепиано, вечерние, скидка"
    )

    # Статусы системы
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    is_active = models.BooleanField("Активен", default=True)
    is_deleted = models.BooleanField("Удален", default=False, editable=False)
    deleted_at = models.DateTimeField("Дата удаления", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['status', '-last_interaction_date']),
            models.Index(fields=['is_active', 'status']),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def save(self, *args, **kwargs):
        # Автообновление silent_days
        if self.last_interaction_date:
            from django.utils import timezone
            self.silent_days = (timezone.now().date() - self.last_interaction_date).days
        super().save(*args, **kwargs)
    
    def update_status(self):
        """Обновить статус на основе последнего взаимодействия"""
        from django.utils import timezone
        
        if not self.last_interaction_date:
            return
        
        silent_days = (timezone.now().date() - self.last_interaction_date).days
        
        if silent_days > 30:
            self.status = 'LOST'
        elif silent_days > 14:
            self.status = 'SILENT'
        elif self.status in ['SILENT', 'LOST']:
            self.status = 'ACTIVE'
        
        self.save(update_fields=['status', 'silent_days'])

class ContactPerson(models.Model):
    """Дополнительные контакты для клиента (например, второй родитель)"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='additional_contacts', verbose_name="Клиент")
    name = models.CharField("ФИО контакта", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    relation = models.CharField("Кем приходится", max_length=50, blank=True, help_text="Например: Мама, Папа")
    is_primary = models.BooleanField("Основной контакт", default=False)

    class Meta:
        verbose_name = "Контактное лицо"
        verbose_name_plural = "Контактные лица"

    def __str__(self):
        return f"{self.name} ({self.client})"

class EmployeeProfile(models.Model):
    """Расширенный профиль сотрудника (преподавателя/менеджера)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    
    # Основные данные
    phone = models.CharField("Рабочий телефон", max_length=20, blank=True)
    bio = models.TextField("О себе", blank=True)
    hire_date = models.DateField("Дата приема", null=True, blank=True)

    # Профиль работы
    instruments = models.CharField("Инструменты", max_length=200, blank=True, help_text="Через запятую: Фортепиано, Гитара")
    hourly_rate = models.DecimalField("Ставка за час", max_digits=10, decimal_places=2, null=True, blank=True)

    # Связь с ролью
    primary_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profiles',
        verbose_name="Основная роль",
        help_text="Текущая рабочая роль"
    )
    
    can_manage_rooms = models.BooleanField("Управление аудиториями", default=False)
    can_manage_resources = models.BooleanField("Управление оборудованием", default=False)
    
    # Статус
    is_active = models.BooleanField("Активен", default=True)
    is_on_leave = models.BooleanField("В отпуске/на больничном", default=False)
    leave_end_date = models.DateField("Конец отпуска/больничного", null=True, blank=True)
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class Room(models.Model):
    """Аудитории и помещения"""
    TYPE_CHOICES = [
        ('STUDIO', 'Студия'),
        ('CLASSROOM', 'Учебный класс'),
        ('PRACTICE', 'Кабинет практики'),
        ('MEETING', 'Зал для совещаний'),
        ('OTHER', 'Другое'),
    ]
    
    name = models.CharField("Название", max_length=100, help_text="Например: Студия 1, Класс А-101")
    type = models.CharField("Тип", max_length=20, choices=TYPE_CHOICES, default='CLASSROOM')
    capacity = models.PositiveIntegerField("Вместимость", default=1, help_text="Максимум человек одновременно")
    description = models.TextField("Описание", blank=True, help_text="Особенности помещения")
    
    # Статус
    is_active = models.BooleanField("Активна", default=True)
    is_available = models.BooleanField("Доступна для записи", default=True)
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Resource(models.Model):
    """Оборудование и ресурсы"""
    TYPE_CHOICES = [
        ('EQUIPMENT', 'Оборудование'),
        ('INSTRUMENT', 'Музыкальный инструмент'),
        ('SOFTWARE', 'Программное обеспечение'),
        ('MATERIAL', 'Расходные материалы'),
        ('OTHER', 'Другое'),
    ]
    
    name = models.CharField("Название", max_length=200, help_text="Например: Микшерный пульт Mackie, Пианино Yamaha")
    type = models.CharField("Тип", max_length=20, choices=TYPE_CHOICES, default='EQUIPMENT')
    quantity = models.PositiveIntegerField("Количество", default=1, help_text="Сколько единиц доступно")
    description = models.TextField("Описание", blank=True)
    
    # Состояние
    condition = models.CharField("Состояние", max_length=20, default='GOOD', choices=[
        ('GOOD', 'Хорошее'),
        ('FAIR', 'Удовлетворительное'),
        ('BAD', 'Требует ремонта'),
        ('MAINTENANCE', 'В ремонте'),
    ])
    
    # Статус
    is_active = models.BooleanField("Активно", default=True)
    is_available = models.BooleanField("Доступно", default=True)
    
    # Стоимость аренды (если применимо)
    rental_price = models.DecimalField("Цена аренды/час (руб)", max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Ресурс"
        verbose_name_plural = "Ресурсы"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (x{self.quantity})"


# Связь ресурсов с аудиторией (многие ко многим)
Room.resources = models.ManyToManyField(
    'Resource',
    related_name='rooms',
    blank=True,
    through='RoomResource'
)


class RoomResource(models.Model):
    """Связь аудиторий и ресурсов (с количеством в конкретной аудитории)"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_resources')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='room_resources')
    quantity_in_room = models.PositiveIntegerField("Количество в этой аудитории", default=1)
    
    class Meta:
        verbose_name = "Ресурс в аудитории"
        verbose_name_plural = "Ресурсы в аудиториях"
        unique_together = ['room', 'resource']

    def __str__(self):
        return f"{self.room.name} - {self.resource.name} (x{self.quantity_in_room})"


# Обновляем связь
Room.resources.through = RoomResource