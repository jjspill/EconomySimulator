import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import interactive
from IPython.display import HTML
from IPython import display
import random
import numpy as np
import os
import time

class bank_account():
    def __init__(self, bank, person, amount, interest_rate, confidence):
        self.bank = bank
        self.person = person
        self.amount = amount
        self.interest_rate = interest_rate
        self.confidence = confidence

class loan():
    def __init__(self, bank, recipient, type, amount, interest_rate, months):
        # can add an amount paid? or does that not matter.
        self.bank = bank
        self.recipient = recipient
        self.recipient_type = type
        self.amount = amount + (amount * interest_rate)
        self.interest_rate = interest_rate
        self.monthly_payment = (amount + (amount * interest_rate)) / months
        self.monthly_payment_no_interest = amount / months

def print_node_attributes(G):
    banks = []
    people = []
    businesses = []

    for node, data in G.nodes(data=True):
        if data['type'] == 'bank':
            banks.append((node, data))
        elif data['type'] == 'person':
            people.append((node, data))
        elif data['type'] == 'a_business':
            businesses.append((node, data))

    print("\nBanks:")
    for node, data in banks:
        print(f"{node}: {data}")

    print("\nPeople:")
    for node, data in people:
        print(f"{node}: {data}")

    print("\nBusinesses:")
    for node, data in businesses:
        print(f"{node}: {data}")

def initialize(num_banks, num_people, num_businesses, bank_interest_rate):
    G = nx.MultiGraph()

    # add the fed
    # G.add_node("THE FED",
    #            type='fed',
    #            )

    # Add bank nodes
    for i in range(num_banks):
        # bank name is bank_n. CHANGE LATER
        bank_name = f'bank_{i+1}'
        # bank_cash = np.random.normal(1_000_000, 200_000)
        bank_cash = 100
        G.add_node(bank_name,
                   type='bank',
                   cash = bank_cash,
                   loaned_money=1,
                   accounts = [],
                   loans = [],
                   crash = False)

    # Add person nodes
    for i in range(num_people):
        # person name is guy_n. CHANGE LATER
        person_name = f'guy_{i+1}'
        # random income from $20,000 to 200,000
        # income = np.random.normal(5000, 500)
        income = random.uniform(10, 30)
        # random initial net_worth (CAN SCALE WITH INCOME)
        # net_worth = np.random.normal(income*12, 6000)
        net_worth = 100
        # initialize first bank account
        initial_bank_account = bank_account(f'bank_{random.randint(1, num_banks)}',
                                            person_name,
                                            random.randint(int(net_worth*0.2), int(net_worth*0.8)),
                                            bank_interest_rate,
                                            0.5)
        # initial_cash = np.random.normal(income, 1_000)
        initial_cash = 50

        G.add_node(person_name,
                   type='person',
                   income=income,
                   bank_accounts=[initial_bank_account],
                   net_worth=net_worth,
                   loans = [],
                   cash = initial_cash,
                   initial_worth=net_worth)

        # add edge from created person to their initial bank
        G.add_edge(initial_bank_account.person,
                   initial_bank_account.bank)
        G.nodes[initial_bank_account.bank]['accounts'].append(initial_bank_account)

    # Add business nodes
    for i in range(num_businesses):
        # business name is business_1. CHANGE LATER
        business_name = f'business_{i+1}'
        # cash = np.random.normal(100_000, 20_000)
        cash = random.randint(30, 90)
        # total_evaluation = np.random.normal(10_000_000, 1_000_000)
        total_evaluation = random.uniform(1, 2)*cash

        G.add_node(business_name,
                   type='a_business',
                   cash=cash,
                   total_worth=total_evaluation,
                   loans=[])
    print_node_attributes(G)
    return G

# if person is low on cash, withdraws money from bank account and adds it to person's cash
def withdraw_money(person):
    if person['cash'] / person['net_worth'] < 0.1:
        account = random.choice(person['bank_accounts'])
        amount = account.amount * random.uniform(0.1, 0.9)
        account.amount -= amount
        person['cash'] += amount
        return amount

# random amount of money goes to cash, leftover goes to a random bank account
def pay_wage(person, spending_scale):
    random.choice(person['bank_accounts']).amount += person['income'] * spending_scale
    person['net_worth'] += person['income']

# todo work on how paid affects montly_payment_no_interest
def collect_loans(bank, G):
    print("COLLECTING LOANS")
    # take loans from peoples cash then bank accounts
    for loan in bank['loans']:
        if loan.recipient_type == 'person':
            # check to see if they can afford with cash
            print("Person Monthly Payment:" + str(loan.monthly_payment))
            if G.nodes[loan.recipient]['cash'] >= loan.monthly_payment:
                G.nodes[loan.recipient]['cash'] -= loan.monthly_payment
                bank['loaned_money'] -= loan.monthly_payment_no_interest
                bank['cash'] += loan.monthly_payment
                loan.amount -= loan.monthly_payment
            else:
                # cycle accounts
                paid = False
                for bank_account in G[loan.recipient]['bank_accounts']:
                    # see if one can pay the loan
                    if bank_account.amount >= loan.monthly_payment:
                        bank_account.amount -= loan.monthly_payment
                        bank['loaned_money'] -= loan.monthly_payment_no_interest
                        bank['cash'] += loan.monthly_payment
                        loan.amount -= loan.monthly_payment
                        paid = True
                        break

                # if one account can't pay
                if not paid:
                    # keep track of amount person can pay
                    can_pay_total = 0
                    # cycle through accounts until person can pay
                    while can_pay_total != loan.monthly_payment:
                        # keep track of how much more money person needs to pay
                        money_needed = loan.monthly_payment
                        # cycle through accounts
                        for bank_account in G[loan.recipient]['bank_accounts']:
                            # if account can pay the rest of the loan
                            if bank_account.amount < money_needed:
                                money_needed -= bank_account.amount
                                can_pay_total += bank_account.amount
                                bank_account.amount = 0
                                G.remove_edge(bank_account.bank, bank_account.person)
                                G.nodes[loan.recipient]['bank_accounts'].remove(bank_account)
                            else:
                                bank_account.amount -= money_needed
                                can_pay_total += money_needed
                                paid = True
                                break

                    if paid:
                        bank['loaned_money'] -= loan.monthly_payment_no_interest
                        bank['cash'] += loan.monthly_payment
                        loan.amount -= loan.monthly_payment
                    else:
                        bank['loaned_money'] -= can_pay_total
                        bank['cash'] += can_pay_total
                        loan.amount -= can_pay_total

        else:
            # take from businesses cash
            #print("Business Monthly Payment:" + str(loan.monthly_payment))
            G.nodes[loan.recipient]['cash'] -= loan.monthly_payment
            bank['loaned_money'] -= loan.monthly_payment_no_interest
            bank['cash'] += loan.monthly_payment
            loan.amount -= loan.monthly_payment

        if loan.amount <= 0:
            G.remove_edge(loan.recipient, loan.bank)
            bank['loans'].remove(loan)

def find_best_bank(G):
    # find the bank with biggest cash to loan ratio
    best_bank = None
    best_bank_ratio = 0
    for node, data in G.nodes(data=True):
        if data['type'] == 'bank':
            if (data['cash'] / data['loaned_money']) > best_bank_ratio:
                best_bank = (node, data)
                best_bank_ratio = data['cash'] / data['loaned_money']
    return best_bank

# busines has a 5% chance to take a loan or a 5% chance to buy supplies
def buy_supplies(business, business_data, G, spending_scale):
    if random.uniform(0, 1) < .05:
        bank = find_best_bank(G)
        if not bank:
            return

        interest_rate = .002
        duration = random.randint(1, 12)

        make_loan(G, bank[0], bank[1], business, business_data, 'business', interest_rate, duration)

    # 5% chance to buy supplies
    if business_data['cash'] >= 100 and random.uniform(0, 1) < 0.2:
        cost = random.uniform(0, business_data['cash'] * spending_scale * 0.7)
        business_data['cash'] -= cost
        #business['total_worth'] += cost


def person_takes_loan(person, person_data, G):
    bank = find_best_bank(G)
    if not bank:
        return

    interest_rate = .002
    duration = random.randint(6, 12)

    make_loan(G, bank[0], bank[1], person, person_data, 'person', interest_rate, duration)

# person buys things with their cash or bank accounts until they have 0 net worth
def buy_things(person, spending_scale):
    # cost is between 50-100% of their monthly income
    fraction = random.uniform(0.5 * spending_scale, 1 * spending_scale)
    cost = person['income'] * fraction
    businesses = []
    if person['cash'] >= cost:
        person['cash'] -= cost
        person['net_worth'] -= cost
        for node, data in G.nodes(data=True):
            if data['type'] == 'a_business':
                businesses.append((node, data))
        (node, data) = random.choice(businesses)
        data['cash'] += cost
    # If they cannot pay for it with cash, pull it out of a bank account.
    else:
        for bank_account in person['bank_accounts']:
            if bank_account.amount >= cost:
                bank_account.amount -= cost
                person['net_worth'] -= cost
                for node, data in G.nodes(data=True):
                    if data['type'] == 'a_business':
                        businesses.append((node, data))
                (node, data) = random.choice(businesses)
                data['cash'] += cost
                return
            else:
                cost -= bank_account.amount
                bank_account.amount = 0
                person['net_worth'] -= bank_account.amount
                for node, data in G.nodes(data=True):
                    if data['type'] == 'a_business':
                        businesses.append((node, data))
                (node, data) = random.choice(businesses)
                data['cash'] += cost

                # this bank account has been drained.

def make_loan(G, bank_node, bank_data, person_business_node, person_business_data, type, interest_rate, duration):
    # if person already has a loan with that bank, return
    if G.has_edge(bank_node, person_business_node):
        return

    # calculate loan amount
    loan_amount = amount_can_loan(bank_data)
    if loan_amount <= 0:
        print("BANK CANT LOAN RIGHT NOW")
        return

    if loan_amount > bank_data['cash']:
        print("BANK CANT LOAN THAT MUCH IT WILL GO UNDER")
        return

    if ((loan_amount + (loan_amount * interest_rate)) / duration) <= 0:
        print("PAYMENT NEGATIVEEEEEE ?!?!?!?!?!?!?")
        return

    print("LOAN AMOUNT: " + str(loan_amount))
    new_loan = loan(bank_node, person_business_node, type, loan_amount, interest_rate, duration)
    print("LOAN AMOUNT: " + str(new_loan.amount))
    print("Loan monthly payment: " + str(new_loan.monthly_payment))

    # update bank and person/business data
    bank_data['cash'] -= loan_amount
    bank_data['loaned_money'] += loan_amount

    person_business_data['cash'] += loan_amount
    if type == 'person':
        person_business_data['net_worth'] += loan_amount

    G.add_edge(person_business_node, bank_node)

    print("MADE A LOAN")
    person_business_data['loans'].append(new_loan)
    bank_data['loans'].append(new_loan)

    return new_loan


def fault_tolerance(G, bank, bank_data, interest_rate):
    # if their cash / loan ratio is more than 40%, too much cash!
    if bank_data['cash'] / bank_data['loaned_money'] > 0.4:
        # loan out the cash
        businesses = []
        for node, data in G.nodes(data=True):
            if data['type'] == 'a_business':
                businesses.append((node, data))
        (node, data) = random.choice(businesses)
        if G.has_edge(bank, node):
            return

        if data['type'] == 'a_business':
            # business does not have enough cash. Set at 5%
            # if data['cash'] / data['total_worth'] < 0.05:
            # invest in business
            loan_cash = max((bank_data['cash'] * .7) - bank_data['loaned_money'],
                             (bank_data['loaned_money'] * .7) - bank_data['cash'])
            new_loan = loan(bank, node, 'business', loan_cash, interest_rate, 30)
            bank_data['loans'].append(new_loan)
            data['loans'].append(new_loan)
            bank_data['cash'] -= loan_cash
            bank_data['loaned_money'] += loan_cash
            G.add_edge(node, bank)
            data['cash'] += loan_cash
            return

    # if their cash / loan ratio is less than 10%, too many loans!
    elif bank_data['cash'] / bank_data['loaned_money'] < 0.1:
        print(bank_data['cash'])
        print(bank_data['loaned_money'])
        new_bank = None
        desired_loan_amount = bank_data['loaned_money'] * 0.1
        best_loan_amount = 0
        # find another bank to loan from
        for node, data in G.nodes(data=True):
            if data['type'] == 'bank' and node != bank:
                loan_amount = amount_can_loan(data)
                if loan_amount > best_loan_amount and abs(desired_loan_amount - loan_amount) < abs(desired_loan_amount - best_loan_amount):
                    best_loan_amount = loan_amount
                    new_bank = node
        # loan from another bank
        if new_bank is not None:
            # get transfer amount
            new_loan = loan(new_bank, bank, 'bank', best_loan_amount, .0001, 30)
            G.nodes[new_bank]['loans'].append(new_loan)
            G.nodes[new_bank]['cash'] -= best_loan_amount
            G.nodes[new_bank]['loaned_money'] += best_loan_amount
            G.add_edge(new_bank, bank)
            bank_data['cash'] -= best_loan_amount
            bank_data['loaned_money'] += best_loan_amount
        # if we cannot loan from another bank, we crash.
        else:
            bank_data['crash'] = True


def amount_can_loan(bank_data):
    cash_to_loaned_ratio = bank_data['cash'] / bank_data['loaned_money']

    if cash_to_loaned_ratio > 0.3:
        target_ratio = 0.25
    elif cash_to_loaned_ratio < 0.05:
        return 0
    else:
        target_ratio = 0.1  # Changed from 0.05 to be more conservative

    max_amount_to_loan = bank_data['cash'] - (bank_data['loaned_money'] * target_ratio) / (1 - target_ratio)

    # Introduce some randomness in the amount the bank can loan
    max_loan_pct = 0.7  # Changed from 0.9 to be more conservative
    min_loan_pct = 0.4  # Changed from 0.6 to be more conservative
    loan_pct = random.uniform(min_loan_pct, max_loan_pct)
    amount_to_loan = max_amount_to_loan * loan_pct

    # Make sure the bank does not loan more than it can afford to lose
    if amount_to_loan > bank_data['cash']:
        amount_to_loan = bank_data['cash']

    # Set a minimum loan amount to prevent the bank from issuing too many super small loans
    min_loan_amount = 10
    if amount_to_loan < min_loan_amount:
        return 0

    return max(amount_to_loan, 0)


def bank_crash(bank, bank_data):
    # Remove all edges from the crashed bank to other nodes in the graph
    print("BANK", bank, "CRASHED. FINAL STATS: ", bank_data)
    time.sleep(15)
    # CHANGED TO EXIT 1 BECAUSE CRASHING BEHAVIOR WAS UNSTABLE
    exit(1)

def check_accounts(G, person, person_data):
    if person_data['cash'] > person_data['net_worth'] * 0.5:

        excess_cash = (person_data['net_worth'] - person_data['cash']) * 0.5

        # 30% chance they deposit their money in a new account
        if person_data['bank_accounts'] and random.random() < 0.7:
            print("PUTTING", excess_cash, "IN THE BANK")
            # Increase cash amount in an existing bank account
            old_bank_account = random.choice(person_data['bank_accounts'])
            old_bank_account.amount += excess_cash
            person_data['cash'] -= excess_cash
            G.nodes[old_bank_account.bank]['cash'] += excess_cash

        else:
            # Create a new bank account and deposit excess cash
            new_bank = None
            for node, data in G.nodes(data=True):
                if data['type'] == 'bank':
                    # Check if person already has an account in this bank
                    existing_bank_account = next((account for account in person_data['bank_accounts'] if account.bank == node), None)
                    if not existing_bank_account:
                        new_bank = node
                        break
            if not new_bank:
                return

            # Create a new bank account and add it to the person's bank accounts
            print("PUTTING", excess_cash, "IN A NEW BANK")
            new_bank_account = bank_account(new_bank, person, excess_cash, 0.002, 1)
            G.add_edge(new_bank, person)
            person_data['bank_accounts'].append(new_bank_account)
            G.nodes[new_bank]['accounts'].append(new_bank_account)


def change_interest(interest_rate, business_average, bank_average, person_average):
    total_average_cash = business_average + bank_average + person_average
    weighted_business_average = business_average / total_average_cash
    weighted_bank_average = bank_average / total_average_cash
    weighted_person_average = person_average / total_average_cash

    # businesses and people have more  money. Raise the interest rate!
    if weighted_bank_average * 2 < (weighted_business_average + weighted_person_average):
        print("CHANGED INTEREST RATE TO", interest_rate + 0.025, "BECAUSE BUSINESSES ARE SPENDING MORE")
        interest_rate += 0.025

    # banks have more money. Lower the interest rate!
    if weighted_bank_average * 2 > (weighted_business_average + weighted_person_average):
        print("CHANGED INTEREST RATE TO", interest_rate - 0.025, "BECAUSE BANKS ARE SPENDING MORE")
        interest_rate -= 0.025
    interest_rate += random.choice([-0.025, 0.025])
    if interest_rate < 0.03:
        interest_rate = 0.03
    elif interest_rate > 0.18:
        interest_rate = 0.18
    return interest_rate

def get_spending(interest_rate):
    return 1.2 - (interest_rate - 0.03) * (1.2 - 0.8) / (0.18 - 0.03)

def update(frame, G, ax1, ax2, ax3, historical_avg_cash, historical_interest_rate, randomness, max_loans):
    global interest_rate
    print("UPDATED")
    # Loop through all nodes ONCE each timestep
    # MAKE SURE WE RESOLVE ALL INDIVIDUAL NODES ACCOUNTS EACH LOOP ITERATION

    node_colors = []
    node_sizes = []

    bank_cash_values = []
    bank_loan_values = []
    business_cash_values = []
    person_cash_values = []

    spending_scale = get_spending(interest_rate)

    for node, data in G.nodes(data=True):
        node_type = data['type']
        # If this is a person node
        if node_type == 'person':
            # get paid their wage
            pay_wage(data, spending_scale)

            # buy things with their money
            buy_things(data, spending_scale)

            # 3% chance any game tick that somebody takes out a big loan.
            if randomness and random.uniform(0, 1) < 0.03:
                person_takes_loan(node, data, G)

            # withdraw money
            withdraw_money(data)

            check_accounts(G, node, data)

            # add node appearance data
            node_colors.append('green')
            node_sizes.append(max(data['cash'], 100))

            person_cash_values.append(data['cash'])

        # If this is a bank node
        elif node_type == 'bank':
            # check our bounds.
            # pay out interest
            collect_loans(data, G)

            # make sure loaned money is not negative (screws up calculations)
            if data['loaned_money'] < 0:
                data['loaned_money'] = 1


            fault_tolerance(G, node, data, interest_rate)

            if data['crash'] and frame > 13:
                bank_crash(node, data)

            # add node appearance data
            node_colors.append('blue')
            node_sizes.append(max(data['cash'], 100))

            bank_cash_values.append(data['cash'])
            bank_loan_values.append(data['loaned_money'])

        elif node_type == 'a_business':

            # do business stuff
            buy_supplies(node, data, G, spending_scale)

            # check bounds
            # add node appearance data
            node_colors.append('red')
            node_sizes.append(200)

            business_cash_values.append(data['cash'])

            continue

        else:
            print("this nodes type is:", node_type, "and we did not account for that")
            node_colors.append('grey')
            node_sizes.append(300)

    avg_bank_cash = np.mean(bank_cash_values)
    avg_bank_loans = np.mean(bank_loan_values)
    avg_business_cash = np.mean(business_cash_values)
    avg_person_cash = np.mean(person_cash_values)

    interest_rate = change_interest(interest_rate, avg_business_cash, avg_bank_cash, avg_person_cash)
    # interest_rate = 0.03


    ax1.clear()
    #print_node_attributes(G)
    nx.draw_networkx(G,
                     pos,
                     with_labels=True,
                     ax=ax1,
                     node_color=node_colors,
                     node_size=node_sizes,
                     font_size=10)

    historical_avg_cash.append([avg_bank_cash, avg_business_cash, avg_person_cash, avg_bank_loans])
    data = np.array(historical_avg_cash).T
    ax2.clear()
    for i, label in enumerate(['Bank Cash', 'Business', 'Person', 'Bank Loans']):
        ax2.plot(data[i], label=label)
    ax2.set_ylim([0, np.max(data) * 1.2])
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Average Money')
    ax2.legend()

    historical_interest_rate.append(interest_rate)
    print(historical_interest_rate)
    ax3.clear()
    ax3.plot(historical_interest_rate, label='Interest Rate', color='r')
    ax3.set_ylim([0, .4])
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Interest Rate (%)')
    ax3.legend()



num_banks = 5
num_people = 10
num_businesses = 5
bank_interest_rate = 0.002
max_loans = 10
randomness = False
historical_avg_cash = []
historical_interest_rate = []
interest_rate = .07

G = initialize(num_banks, num_people, num_businesses, bank_interest_rate)

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
pos = nx.multipartite_layout(G, scale=5.0, subset_key='type')

interactive(False)
ani = FuncAnimation(fig, update, frames=120, fargs=(G, ax1, ax2, ax3, historical_avg_cash, historical_interest_rate, randomness, max_loans), interval=1000, repeat=False)

plt.show()