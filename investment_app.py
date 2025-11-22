import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Investment Comparison App", layout="wide")

st.title("📊 Investment Comparison: Stocks vs Real Estate")
st.write("""
This interactive app lets you compare long-term stock investing with real estate investing. 
You can adjust all parameters, including whether expenses are entered as percentages or fixed amounts. 
The summary and graphs update instantly as you change the inputs!
""")

# --- Sidebar: User Inputs ---
st.sidebar.header("Investment Parameters")

# --- Stock Parameters ---
st.sidebar.subheader("Stock Investment")
initial_investment = st.sidebar.number_input("Initial Investment ($)", 1000, 1000000, 16000, 1000)
monthly_contribution = st.sidebar.number_input("Monthly Contribution ($)", 0, 20000, 4000, 100)
annual_return = st.sidebar.number_input("Expected Annual Return (%)", 0.0, 20.0, 10.0, 0.1) / 100
stock_years = st.sidebar.number_input("Investment Duration (Years)", 1, 40, 30, 1)

# --- Real Estate Parameters ---
st.sidebar.subheader("Real Estate Investment")
down_payment = st.sidebar.number_input("Down Payment ($)", 0, 1000000, 16000, 1000)
property_value = st.sidebar.number_input("Property Value ($)", 10000, 2000000, 365000, 1000)
down_payment_percent = down_payment / property_value if property_value else 0
closing_costs = st.sidebar.number_input("Closing Costs ($)", 0, 100000, int(0.03 * property_value), 100)

# --- Mortgage Parameters ---
mortgage_rate = st.sidebar.number_input("Mortgage Rate (%)", 0.0, 20.0, 6.68, 0.01) / 100
loan_term_years = st.sidebar.number_input("Loan Term (Years)", 1, 40, 30, 1)

# --- Property Expenses ---
st.sidebar.subheader("Property Expenses")
monthly_rent = st.sidebar.number_input("Monthly Rent (or Savings) ($)", 0, 20000, 2499, 1)

# --- Utilities ---
st.sidebar.subheader("Utilities")
monthly_utilities = st.sidebar.number_input("Monthly Utilities ($)", 0, 20000, 0, 1)

# Helper for percent/amount toggle
def percent_or_amount(label, default_rate, default_amount, min_rate=0.0, max_rate=1.0, min_amt=0, max_amt=10000, step=0.01):
    mode = st.sidebar.radio(f"{label} Input Mode", ["Percent", "Amount"], key=label)
    if mode == "Percent":
        rate = st.sidebar.number_input(f"{label} (%)", min_rate*100, max_rate*100, default_rate*100, step*100) / 100
        amount = None
    else:
        rate = None
        amount = st.sidebar.number_input(f"{label} ($)", min_amt, max_amt, default_amount, 1)
    return rate, amount

monthly_property_taxes_rate, monthly_property_taxes_amount = percent_or_amount("Property Taxes", 0.01, 0)
monthly_insurance_rate, monthly_insurance_amount = percent_or_amount("Insurance", 0.0, 208)
monthly_maintenance_rate, monthly_maintenance_amount = percent_or_amount("Maintenance", 0.01, 0)
monthly_management_rate, monthly_management_amount = percent_or_amount("Management", 0.06, 0)
monthly_vacancy_rate, monthly_vacancy_amount = percent_or_amount("Vacancy", 0.06, 0)
monthly_hoa_rate, monthly_hoa_amount = percent_or_amount("HOA", 0.0, 0)

# --- PMI Parameters ---
pmi_rate = st.sidebar.number_input("PMI Rate (%)", 0.0, 5.0, 1.0, 0.01) / 100

# --- Appreciation & Growth ---
st.sidebar.subheader("Growth Assumptions")
property_appreciation_rate = st.sidebar.number_input("Property Appreciation Rate (%)", 0.0, 10.0, 3.0, 0.1) / 100
rental_growth_rate = st.sidebar.number_input("Rental Growth Rate (%)", 0.0, 10.0, 3.0, 0.1) / 100

# --- Tax Parameters ---
st.sidebar.subheader("Tax Parameters")
annual_income = st.sidebar.number_input("Annual Income ($)", 0, 1000000, 160000, 1000)
tax_bracket = st.sidebar.number_input("Federal Tax Rate (%)", 0.0, 50.0, 24.0, 0.1) / 100
state_tax_rate = st.sidebar.number_input("State Tax Rate (%)", 0.0, 20.0, 5.0, 0.1) / 100

total_tax_rate = tax_bracket + state_tax_rate

# --- Calculated Parameters ---
monthly_return = annual_return / 12
months = stock_years * 12
loan_amount = property_value - down_payment
loan_term_months = loan_term_years * 12
monthly_rate = mortgage_rate / 12
depreciation_per_year = property_value / 27.5
monthly_depreciation = depreciation_per_year / 12
total_upfront = down_payment + closing_costs

# --- Monthly Expenses Calculation ---
def get_expense(rate, amount, base):
    if amount is not None and amount > 0:
        return amount
    elif rate is not None and rate > 0:
        return base * rate if base else 0
    else:
        return 0

monthly_property_taxes = (get_expense(monthly_property_taxes_rate, monthly_property_taxes_amount, property_value) / 12) or 0
monthly_insurance = (get_expense(monthly_insurance_rate, monthly_insurance_amount, property_value) / 12) or 0
monthly_maintenance = (get_expense(monthly_maintenance_rate, monthly_maintenance_amount, property_value) / 12) or 0
monthly_management = (get_expense(monthly_management_rate, monthly_management_amount, monthly_rent)) or 0
monthly_vacancy = (get_expense(monthly_vacancy_rate, monthly_vacancy_amount, monthly_rent)) or 0
monthly_hoa = (get_expense(monthly_hoa_rate, monthly_hoa_amount, property_value) / 12) or 0

# --- Stock Investment Calculation ---
def calculate_stock_investment(initial, monthly, rate, periods):
    values = []
    current_value = initial
    for month in range(1, periods + 1):
        current_value += monthly
        current_value *= (1 + rate)
        values.append(current_value)
    return values

stock_values = calculate_stock_investment(initial_investment, monthly_contribution, monthly_return, months)

# --- Real Estate Calculations ---
monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**loan_term_months) / ((1 + monthly_rate)**loan_term_months - 1) if loan_amount > 0 else 0
monthly_mortgage = monthly_payment or 0
monthly_pmi = ((loan_amount * pmi_rate) / 12 if loan_amount > 0 else 0) or 0
total_monthly_expenses = (monthly_mortgage + monthly_property_taxes + monthly_insurance + monthly_maintenance + monthly_management + monthly_vacancy + monthly_pmi + monthly_hoa + monthly_utilities)
monthly_cash_flow = monthly_rent - total_monthly_expenses

# Helper: Calculate remaining loan balance after n payments (months)
def remaining_loan_balance(principal, rate, total_payments, payments_made):
    if rate == 0:
        return max(principal - (principal / total_payments) * payments_made, 0)
    r = rate
    n = total_payments
    p = payments_made
    return principal * (((1 + r) ** n - (1 + r) ** p) / ((1 + r) ** n - 1))

# --- Real Estate Calculations ---
def calculate_real_estate_value(initial_value, monthly_rent, appreciation_rate, rental_growth_rate, years, loan_amount, pmi_rate, total_tax_rate, monthly_depreciation):
    annual_data = []
    current_value = initial_value
    current_monthly_rent = monthly_rent
    for year in range(1, years + 1):
        current_value *= (1 + appreciation_rate)
        current_monthly_rent *= (1 + rental_growth_rate)
        payments_made = year * 12
        current_loan_balance = remaining_loan_balance(loan_amount, monthly_rate, loan_term_months, payments_made)
        current_equity_percent = (current_value - current_loan_balance) / current_value if current_value else 0
        current_equity_dollars = current_value - current_loan_balance
        if current_equity_percent < 0.20:
            current_monthly_pmi = (loan_amount * pmi_rate) / 12 if loan_amount > 0 else 0
        else:
            current_monthly_pmi = 0
        # Approximate monthly mortgage interest for this year
        interest_paid_year = 0
        for m in range(12):
            bal = remaining_loan_balance(loan_amount, monthly_rate, loan_term_months, (year-1)*12 + m)
            interest_paid_year += bal * monthly_rate
        monthly_mortgage_interest = interest_paid_year / 12
        monthly_deductible_expenses = (monthly_mortgage_interest + monthly_property_taxes + monthly_insurance + monthly_maintenance + monthly_management + current_monthly_pmi + monthly_depreciation + monthly_hoa)
        monthly_tax_savings = monthly_deductible_expenses * total_tax_rate
        net_monthly_cash_flow = monthly_rent - total_monthly_expenses + monthly_tax_savings
        annual_data.append({
            'year': year,
            'property_value': current_value,
            'monthly_rent': current_monthly_rent,
            'annual_rent': current_monthly_rent * 12,
            'equity_percent': current_equity_percent * 100,
            'equity_dollars': current_equity_dollars,
            'monthly_pmi': current_monthly_pmi,
            'monthly_tax_savings': monthly_tax_savings,
            'net_monthly_cash_flow': net_monthly_cash_flow,
            'loan_balance': current_loan_balance
        })
    return annual_data

real_estate_data = calculate_real_estate_value(property_value, monthly_rent, property_appreciation_rate, rental_growth_rate, stock_years, loan_amount, pmi_rate, total_tax_rate, monthly_depreciation)

# --- Comparison Table ---
comparison_data = []
for year in range(1, stock_years + 1):
    month_index = year * 12 - 1
    stock_value = stock_values[month_index]
    total_stock_contributions = initial_investment + (monthly_contribution * year * 12)
    stock_gain = stock_value - total_stock_contributions
    re_data = real_estate_data[year - 1]
    total_pmi_paid = sum(real_estate_data[y]['monthly_pmi'] * 12 for y in range(year))
    total_negative_cash_flow = sum(abs(min(y['net_monthly_cash_flow'], 0)) * 12 for y in real_estate_data[:year])
    total_re_investment = total_upfront + total_negative_cash_flow + total_pmi_paid
    re_gain = re_data['equity_dollars'] - total_re_investment
    comparison_data.append({
        'Year': year,
        'Stock_Value': round(stock_value, 2),
        'Stock_Total_Invested': round(total_stock_contributions, 2),
        'Stock_Gain': round(stock_gain, 2),
        'Property_Value': round(re_data['property_value'], 2),
        'RE_Total_Invested': round(total_re_investment, 2),
        'RE_Gain': round(re_gain, 2),
        'Stock_Advantage': round(stock_value - re_data['equity_dollars'], 2),
        'Monthly_Rent': round(re_data['monthly_rent'], 2),
        'Equity_Percent': round(re_data['equity_percent'], 1),
        'Equity_Dollars': round(re_data['equity_dollars'], 2),
        'Monthly_PMI': round(re_data['monthly_pmi'], 2),
        'Monthly_Tax_Savings': round(re_data['monthly_tax_savings'], 2),
        'Net_Monthly_Cash_Flow': round(re_data['net_monthly_cash_flow'], 2)
    })
df = pd.DataFrame(comparison_data)

# --- Summary Section ---
st.header("Investment Comparison Summary (1st Month)")
stock_1_month = stock_values[0] if len(stock_values) > 0 else stock_values[-1]
total_stock_contributions_1m = initial_investment + (monthly_contribution * 1)
stock_gain_1m = stock_1_month - total_stock_contributions_1m
stock_roi_1m = (stock_gain_1m / total_stock_contributions_1m) * 100 if total_stock_contributions_1m else 0
re_data_1y = real_estate_data[0] if len(real_estate_data) > 0 else real_estate_data[-1]
total_pmi_1y = real_estate_data[0]['monthly_pmi'] * 12 if len(real_estate_data) > 0 else 0
total_re_investment_1m = total_upfront + (abs(min(re_data_1y['net_monthly_cash_flow'], 0)) * 1) + re_data_1y['monthly_pmi']
re_gain_1m = re_data_1y['equity_dollars'] - total_re_investment_1m
re_roi_1m = (re_gain_1m / total_re_investment_1m) * 100 if total_re_investment_1m else 0

st.markdown(f"""
**Stock Investment Value (Month 1):** ${stock_1_month:,.0f}  
**Stock Total Invested (Month 1):** ${total_stock_contributions_1m:,.0f}  
**Stock Gain (Month 1):** ${stock_gain_1m:,.0f}  
**Stock ROI (Month 1):** {stock_roi_1m:.1f}%  
**Real Estate Value (Year 1):** ${re_data_1y['property_value']:,.0f}  
**Real Estate Total Invested (Month 1):** ${total_re_investment_1m:,.0f}  
**Real Estate Gain (Month 1):** ${re_gain_1m:,.0f}  
**Real Estate ROI (Month 1):** {re_roi_1m:.1f}%  
**Stock Advantage (Month 1):** ${stock_1_month - re_data_1y['property_value']:,.0f}  
**Monthly Tax Savings (Month 1):** ${re_data_1y['monthly_tax_savings']:.2f}  
**Net Monthly Cash Flow (Month 1):** ${re_data_1y['net_monthly_cash_flow']:.2f}  
**Equity Percentage (Year 1):** {re_data_1y['equity_percent']:.1f}%  
**Equity (Year 1):** ${re_data_1y['equity_dollars']:,.0f}  
""")

with st.expander("Show Monthly Cash Flow Details (Month 1)"):
    st.write(f"Monthly Rent: ${re_data_1y['monthly_rent']:.2f}")
    st.write(f"Monthly Mortgage: ${monthly_mortgage:.2f}")
    st.write(f"Monthly Property Taxes: ${monthly_property_taxes:.2f}")
    st.write(f"Monthly Insurance: ${monthly_insurance:.2f}")
    st.write(f"Monthly Maintenance: ${monthly_maintenance:.2f}")
    st.write(f"Monthly Management: ${monthly_management:.2f}")
    st.write(f"Monthly Vacancy: ${monthly_vacancy:.2f}")
    st.write(f"Monthly PMI: ${re_data_1y['monthly_pmi']:.2f}")
    st.write(f"Monthly HOA: ${monthly_hoa:.2f}")
    st.write(f"Monthly Utilities: ${monthly_utilities:.2f}")
    st.write(f"Total Monthly Expenses: ${monthly_mortgage + monthly_property_taxes + monthly_insurance + monthly_maintenance + monthly_management + monthly_vacancy + re_data_1y['monthly_pmi'] + monthly_hoa + monthly_utilities:.2f}")
    st.write(f"Monthly Tax Savings: ${re_data_1y['monthly_tax_savings']:.2f}")
    st.write(f"Net Monthly Cash Flow: ${re_data_1y['net_monthly_cash_flow']:.2f}")
    st.write(f"Equity (Year 1): ${re_data_1y['equity_dollars']:,.0f}")

# --- Graphs ---
st.header("Investment Growth Over Time")
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
# Graph 1: Total Value Comparison
ax1.plot(df['Year'], df['Stock_Value'], label='Stock Investment', linewidth=2, color='blue')
ax1.plot(df['Year'], df['Property_Value'], label='Real Estate', linewidth=2, color='red')
ax1.set_title('Total Investment Value Over Time', fontsize=14, fontweight='bold')
ax1.set_xlabel('Years')
ax1.set_ylabel('Value ($)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax1.set_xticks(range(0, stock_years+1, 5))
ax1.set_xticklabels(range(0, stock_years+1, 5))
# Graph 2: Total Amount Invested
ax2.plot(df['Year'], df['Stock_Total_Invested'], label='Stock Investment', linewidth=2, color='blue')
ax2.plot(df['Year'], df['RE_Total_Invested'], label='Real Estate', linewidth=2, color='red')
ax2.set_title('Total Amount Invested Over Time', fontsize=14, fontweight='bold')
ax2.set_xlabel('Years')
ax2.set_ylabel('Amount Invested ($)')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax2.set_xticks(range(0, stock_years+1, 5))
ax2.set_xticklabels(range(0, stock_years+1, 5))
# Graph 3: Gains Comparison
ax3.plot(df['Year'], df['Stock_Gain'], label='Stock Investment', linewidth=2, color='blue')
ax3.plot(df['Year'], df['RE_Gain'], label='Real Estate', linewidth=2, color='red')
ax3.set_title('Investment Gains Over Time', fontsize=14, fontweight='bold')
ax3.set_xlabel('Years')
ax3.set_ylabel('Gains ($)')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax3.set_xticks(range(0, stock_years+1, 5))
ax3.set_xticklabels(range(0, stock_years+1, 5))
# Graph 4: Stock Advantage
ax4.plot(df['Year'], df['Stock_Advantage'], label='Stock Advantage', linewidth=2, color='green')
ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax4.set_title('Stock Investment Advantage Over Real Estate', fontsize=14, fontweight='bold')
ax4.set_xlabel('Years')
ax4.set_ylabel('Advantage ($)')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax4.set_xticks(range(0, stock_years+1, 5))
ax4.set_xticklabels(range(0, stock_years+1, 5))
plt.tight_layout()
st.pyplot(fig)

# --- Calculate time to reach 20% equity ---
def months_to_20_percent_equity(property_value, loan_amount, appreciation_rate, monthly_rate, loan_term_months):
    current_value = property_value
    balance = loan_amount
    for month in range(1, loan_term_months + 1):
        # Property appreciates monthly
        current_value *= (1 + appreciation_rate / 12)
        # Mortgage amortization
        interest = balance * monthly_rate
        principal = monthly_mortgage - interest if balance > 0 else 0
        balance = max(balance - principal, 0)
        equity = current_value - balance
        equity_percent = equity / current_value if current_value else 0
        if equity_percent >= 0.20:
            return month
    return None

months_to_20 = months_to_20_percent_equity(property_value, loan_amount, property_appreciation_rate, monthly_rate, loan_term_months)

if months_to_20:
    years_to_20 = months_to_20 // 12
    months_extra = months_to_20 % 12
    st.info(f"It will take about {months_to_20} months ({years_to_20} years and {months_extra} months) to reach 20% equity in your house if you only pay the EMI and make no extra payments.")
else:
    st.info("You will not reach 20% equity within the loan term under the current assumptions.")

st.caption("Graphs and calculations update instantly as you change the parameters above.") 