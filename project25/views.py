from django.shortcuts import render, redirect
from project25.models import *
from decimal import Decimal

def login_view(request):
    if 'username' in request.GET and 'password' in request.GET:
        givenUsername = request.GET['username']
        givenPassword = request.GET['password']
        user = User.objects.filter(username=givenUsername, password=givenPassword).first()
        if user:
            request.session['user_id'] = user.id
            return redirect('/welcome/')     
        else:
            template_values = {'error' : 'User doesnt exit...'}
            return render(request, 'login.html', template_values)
    else:
        return render(request, 'login.html')

def welcome_view(request):
      if 'user_id' not in request.session:
           return redirect('/login/')
      user = User.objects.filter(id=request.session['user_id']).first()
      if not user:
           request.session.flush()
           return redirect('/login/')
      template_values = {'user' : user}
      return render(request, 'welcome.html', template_values)

def register_view(request):
      if 'username' in request.GET and 'password' in request.GET and 'confirmPassword' in request.GET:
            if request.GET['password'] == request.GET['confirmPassword']:
                newUser = User(username=request.GET['username'],
                            password=request.GET['password'])   
                newUser.save()
                return redirect('/login/')
            else:
                template_values = {'error' : 'Given passwords dont match...'}
                return render(request, 'register.html', template_values)
      else:
            return render(request, 'register.html')

def logout_view(request):
     request.session.flush()
     return redirect('/login/')

def group_view(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    # Since the user can only create/view groups that it's in, there's no need to add it to the list
    template_values = {'users' : User.objects.exclude(id=user.id), 'groups' : user.groups.all()}
    return render(request, 'groups.html', template_values)

def create_view(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    if 'name' not in request.GET:
         return redirect('/groups/')
    name = request.GET['name'].strip()
    if not name:
         template_values = {'users' : User.objects.exclude(id=user.id), 'groups' : user.groups.all(), 'error' : 'No group name provided...'}
         return render(request, 'groups.html', template_values)
    members = request.GET.getlist('members')
    new = Group.objects.create(name=name)
    Currency.objects.create(group=new, currency='EUR', rates='1')
    new.members.add(user)
    for member in members:
         new.members.add(member)
    return redirect('/groups/')

def detail_view(request, group_id):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    group = Group.objects.filter(id=group_id).first()
    if not group or not group.members.filter(id=user.id).exists():
         return redirect('/groups/')
    members = group.members.all()
    payments = group.payments.all()
    balances, clearing = calculate_clearing(members, payments)
    template_values = {'group' : group, 'currencies' : group.currencies.all(), 'payments' : payments, 'balances': balances.values(), 'clearing': clearing}
    return render(request, 'detail.html', template_values)


def currency_view(request, group_id):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    group = Group.objects.filter(id=group_id).first()
    if not group or not group.members.filter(id=user.id).exists():
        return redirect('/groups/')
    if 'currency' not in request.GET or 'rates' not in request.GET:
        return redirect('/groups/' + str(group.id) + '/')
    currency = request.GET['currency']
    rates = request.GET['rates']
    existing = Currency.objects.filter(group=group, currency=currency).first()
    if existing:
        return redirect('/groups/' + str(group.id) + '/')
    Currency.objects.create(group=group, currency=currency, rates=rates)
    return redirect('/groups/' + str(group.id) + '/')

def delete_view(request, group_id):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    group = Group.objects.filter(id=group_id).first()
    if not group or not group.members.filter(id=user.id).exists():
        return redirect('/groups/')
    group.delete()
    return redirect('/groups/')

def payment_view(request, group_id):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    group = Group.objects.filter(id=group_id).first()
    if not group or not group.members.filter(id=user.id).exists():
        return redirect('/groups/')
    if ('description' not in request.GET or 'payer' not in request.GET or 'amount' not in request.GET or 'currency' not in request.GET):
        return redirect('/groups/' + str(group.id) + '/')
    description = request.GET['description']
    payer_id = request.GET['payer']
    amount = Decimal(request.GET['amount'])
    currency_id = request.GET['currency']
    beneficiaries = request.GET.getlist('beneficiaries')
    payer = group.members.filter(id=payer_id).first()
    if not payer:
        return redirect('/groups/' + str(group.id) + '/')
    currency = group.currencies.filter(id=currency_id).first()
    if not currency:
        return redirect('/groups/' + str(group.id) + '/')
    selected_benef = []
    for ben_id in beneficiaries:
        beneficiary = group.members.filter(id=ben_id).first()
        if beneficiary:
            selected_benef.append(beneficiary)
    if not selected_benef:
        return redirect('/groups/' + str(group.id) + '/')
    new = Payment.objects.create(group=group, payer=payer, description=description, amount=amount, currency=currency)
    share = new.amount / len(selected_benef)
    for beneficiary in selected_benef:
        new.beneficiaries.add(beneficiary)
        Share.objects.create(payment=new, user=beneficiary, amount=share)
    return redirect('/groups/' + str(group.id) + '/')

def calculate_clearing(members, payments):
    balances = {}
    for member in members:
        balances[member.id] = {'user': member, 'amount': Decimal('0'), 'paid_total': Decimal('0')}
    for payment in payments:
        payment.eur_value = payment.amount * payment.currency.rates
        balances[payment.payer.id]['paid_total'] += payment.eur_value
        balances[payment.payer.id]['amount'] += payment.eur_value
        for share in payment.shares.all():
            share_eur = share.amount * payment.currency.rates
            balances[share.user.id]['amount'] -= share_eur
    debtors = []
    creditors = []
    for balance in balances.values():
        amount = balance['amount']
        if amount < 0:
            debtors.append({'user': balance['user'], 'amount': -amount})
        elif amount > 0:
            creditors.append({'user': balance['user'], 'amount': amount})
    clearing = []
    i = 0
    j = 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        amount = min(debtor['amount'], creditor['amount'])
        clearing.append({'debtor': debtor['user'], 'creditor': creditor['user'], 'amount': amount})
        debtor['amount'] -= amount
        creditor['amount'] -= amount
        if debtor['amount'] == 0:
            i += 1
        if creditor['amount'] == 0:
            j += 1
    return balances.values(), clearing

def global_clearing_view(request):
    if 'user_id' not in request.session:
        return redirect('/login/')
    user = User.objects.filter(id=request.session['user_id']).first()
    if not user:
        request.session.flush()
        return redirect('/login/')
    groups = Group.objects.all()
    # TODO: maybe replace the groups__in
    members = User.objects.filter(groups__in=groups).distinct()
    payments = []
    for group in groups:
        for payment in group.payments.all():
            payments.append(payment)
    balances, clearing = calculate_clearing(members, payments)
    template_values = {'balances' : balances, 'clearing' : clearing}
    return render(request, 'global_clearing.html', template_values)