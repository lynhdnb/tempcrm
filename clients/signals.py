from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Enrollment
from .models import Interaction

@receiver(post_save, sender=Enrollment)
def create_enrollment_interaction(sender, instance, created, **kwargs):
    if created:
        Interaction.objects.create(
            client=instance.client,
            interaction_type='system',
            content=f'Клиент записан на курс «{instance.product.name}»',
            created_by=None  # Системное событие
        )
