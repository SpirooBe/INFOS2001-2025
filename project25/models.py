from django.db import models
    
class User(models.Model):
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=20)

    def __str__(self):
        return self.username

class Group(models.Model):
    name = models.CharField(max_length=20)
    members = models.ManyToManyField(User, related_name='groups')

    def __str__(self):
        return self.name

class Currency(models.Model):
    group = models.ForeignKey(Group, related_name='currencies', on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)
    rates = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return self.currency + " : " + self.group.name

class Payment(models.Model):
    group = models.ForeignKey(Group, related_name='payments', on_delete=models.CASCADE)
    payer = models.ForeignKey(User, related_name='payments_made', on_delete=models.CASCADE)
    beneficiaries = models.ManyToManyField(User, related_name='payments_received')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, related_name='payments', on_delete=models.CASCADE)

    def __str__(self):
        return self.description + " : " + self.group.name

class Share(models.Model):
    payment = models.ForeignKey(Payment, related_name='shares', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='payment_shares', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=8)

    def __str__(self):
        return self.user.username + " : " + str(self.amount)
