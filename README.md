# 2024-2025 INFOS2001 Project implementation

## 0. Scope and Limitations

All features required by the project statement have been implemented, including the optional ones.

Some aspects have deliberately been kept simple to focus on the required functionality. In particular, the application does not aim to provide the security, validation, accounting precision or robustness expected from a real production financial application.

As a cybersecurity major, it would obviously be very easy to implement such security or refinements, but building a perfect web application didn't seem to be the point here.

## 1. Installation and Execution

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Create the database and apply the existing migrations:

```bash
python3 manage.py makemigrations project25
python3 manage.py migrate
```

Create a Django administrator account to access the administration interface:

```bash
python3 manage.py createsuperuser
```

Finally, start the development server:

```bash
python3 manage.py runserver 9000
```

The application is then available at:
```http://127.0.0.1:9000/```

## 2. Main Features

### User management
- User registration with a username and password.
- Login and logout.
- Session-based identification of the currently logged-in user.

### Group management
- Creation of groups.
- Selection of registered users as group members.
- Access to the groups in which a user participates.

### Currency management
- Definition of currencies and exchange rates within individual groups.
- Automatic creation of EUR as the reference currency, with an exchange rate of 1.
- Different exchange rates for the same currency in different groups.

### Expense management
- Recording of expenses, including a description, amount, currency and payer.
- Selection of the members who benefit from each expense.
- Equal or custom allocation of expenses between beneficiaries.

### Clearing and reimbursements
- Calculation of each member's net balance within a group.
- Conversion of amounts into EUR before calculating balances.
- Generation of suggested transfers between debtors and creditors.
- Confirmation of a clearing operation by recording the corresponding reimbursements.

### Individual and global statements
- Display of the total expenses paid by each member.
- Display of the net amount each member should receive or pay.
- Calculation of a global clearing across all groups.

## 3. Implementation Choices

### 3.1. Data model

The application uses five main models: `User`, `Group`, `Currency`, `Payment` and `Share`.

- **User:** represents a registered application user.
- **Group:** represents a group of people sharing expenses. A many-to-many relationship with `User` allows a user to participate in several groups and a group to contain several users.
- **Currency:** represents a currency and its exchange rate within a particular group. The relationship with `Group` ensures that exchange rates are specific to each group.
- **Payment:** represents either an ordinary expense or a reimbursement. It stores the group, payer, amount, currency, description and beneficiaries.
- **Share:** represents the portion of an ordinary expense allocated to an individual beneficiary. Each share is linked to a payment and a user.

This separation allows the application to distinguish between the original expense, the people who benefit from it and the amount allocated to each person.

### 3.2. Group-specific currencies

Currencies are associated with groups rather than being defined globally.

This choice allows the same currency to have different exchange rates in different groups. For example, a USD exchange rate used for one trip does not need to be the same as the rate used for another trip.

All balances are converted into EUR before the clearing calculation. EUR is automatically created for each group with an exchange rate of 1.

Exchange rates represent the EUR value of one unit of the corresponding currency.

### 3.3. Expense allocation

The `Payment` model stores the original expense, while the `Share` model stores how that expense is distributed among its beneficiaries.

This design supports two allocation methods:

- **Equal allocation:** the expense is divided equally between the selected beneficiaries.
- **Custom allocation:** the user specifies the amount allocated to each beneficiary.

Keeping individual shares in a separate model makes it possible to calculate each member's financial position independently of who initially paid the expense.

### 3.4. Reimbursements

Reimbursements are represented using the existing `Payment` model, with the Boolean field `is_reimbursement` distinguishing them from ordinary expenses.

The payer represents the person sending the money, while the beneficiary represents the person receiving it.

Reimbursements do not create `Share` records and are not included in the total expenses paid by a member. Instead, they modify the members' existing balances.

This approach avoids introducing a separate model for reimbursements while reusing the existing payment structure.

### 3.5. Clearing algorithm

The clearing calculation first determines the net balance of each group member.

For ordinary expenses:
- The payer is credited with the full amount paid.
- Each beneficiary is debited by their allocated share.

For reimbursements:
- The sender's balance is increased.
- The recipient's balance is decreased.

After converting the amounts into EUR, the application separates members into debtors and creditors. It then matches debtors with creditors to generate a list of transfers that settles the outstanding balances.

The algorithm uses a straightforward matching approach rather than attempting to find a mathematically optimal solution in every possible case.

### 3.6. Global clearing

The global clearing feature reuses the same clearing algorithm as the group-level calculation.

Instead of considering payments from a single group, it gathers payments from all groups and calculates the resulting balances across them.

This makes it possible to determine the overall financial position of each user, regardless of which group generated the original expenses.

### 3.7. Sessions

Django sessions are used to keep track of the currently logged-in application user.

The user's database ID is stored in the session after successful login. Subsequent requests use this ID to identify the user and retrieve the relevant information.

Logging out clears the session.
