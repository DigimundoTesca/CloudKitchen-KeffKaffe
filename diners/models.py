from django.db import models


class Diner(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=160, default='')
    employee_number = models.CharField(max_length=32, default='')
    RFID = models.CharField(default='', max_length=24)

    class Meta:
        verbose_name = 'Comensal'
        verbose_name_plural = 'Comensales'

    def __str__(self):
        return self.name

class AccessLog(models.Model):
    diner = models.ForeignKey(Diner, null=True, blank=True)
    RFID = models.CharField(default='', max_length=24)
    access_to_room = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Control de Acceso'
        verbose_name_plural = 'Control de Accesos'

    def __str__(self):
        return self.RFID


class ElementToEvaluate(models.Model):
    element = models.CharField(max_length=48, default='', unique=True)

    class Meta:
        verbose_name = "Elemento a evaluar"
        verbose_name_plural = "Elementos a evaluar"

    def __str__(self):
        return self.element


class Suggestion(models.Model):
    suggestion = models.TextField(default='')
    creation_date = models.DateTimeField(auto_now_add=True)
    satisfaction_rating = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Segerencia"
        verbose_name_plural = "Sugerencias"

    def __str__(self):
        text = str(self.suggestion)
        text = (text[:48] + '...') if len(text) > 12 else text
        return text
    
    def shortened_suggestion(self):
        text = str(self.suggestion)
        text = (text[:48] + '...') if len(text) > 12 else text
        return text

class SatisfactionRating(models.Model):
    elements = models.ManyToManyField(ElementToEvaluate)
    satisfaction_rating = models.PositiveIntegerField(default=1)
    creation_date = models.DateTimeField(auto_now_add=True)
    suggestion = models.ForeignKey(Suggestion, null=True, blank=True)


    class Meta:
        verbose_name = "Índice de Satisfacción"
        verbose_name_plural = "Índices de Satisfacción"

    def __str__(self):
        return self.satisfaction_rating
    
