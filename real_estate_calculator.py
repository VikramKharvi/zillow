import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Real Estate Investment Calculator", layout="wide")

st.title("🏠 Real Estate Investment Calculator")
st.write("""
This comprehensive calculator analyzes real estate investment opportunities including purchase analysis, 
income projections, expense calculations, tax implications, and cash flow analysis over time.
""")

# --- Sidebar: Property Purchase Details ---
st.sidebar.header("Property Purchase Details")

# Purchase Information
purchase_price = st.sidebar.number_input("Purchase Price ($)", 10000, 5000000, 360000, 1000)
down_payment = st.sidebar.number_input("Down Payment ($)", 0, purchase_price, 15000, 1000)
loan_amount = purchase_price - down_payment

# Mortgage Details
mortgage_rate = st.sidebar.number_input("Mortgage Rate (%)", 0.0, 20.0, 6.90, 0.01) / 100
loan_term_years = st.sidebar.number_input("Loan Term (Years)", 1, 40, 30, 1)
loan_term_months = loan_term_years * 12
monthly_rate = mortgage_rate / 12

# Calculate monthly mortgage payment
if loan_amount > 0:
    monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**loan_term_months) / ((1 + monthly_rate)**loan_term_months - 1)
else:
    monthly_mortgage = 0

st.sidebar.write(f"**Monthly Mortgage Payment:** ${monthly_mortgage:,.2f}")

# Monthly Loan Contributions
st.sidebar.subheader("Additional Loan Payments")
monthly_loan_contribution = st.sidebar.number_input("Monthly Additional Payment ($)", 0, 10000, 0, 50, 
    help="Additional monthly payment to reduce loan balance faster")
total_monthly_payment = monthly_mortgage + monthly_loan_contribution
st.sidebar.write(f"**Total Monthly Payment:** ${total_monthly_payment:,.2f}")

# Calculate new loan term with additional payments
if monthly_loan_contribution > 0 and loan_amount > 0:
    # Calculate how many payments it would take to pay off the loan with additional payments
    # Using the formula: N = -log(1 - P*r/A) / log(1 + r)
    # where P = principal, r = monthly rate, A = total monthly payment
    if total_monthly_payment > loan_amount * monthly_rate:
        new_loan_term_months = -np.log(1 - loan_amount * monthly_rate / total_monthly_payment) / np.log(1 + monthly_rate)
        new_loan_term_years = new_loan_term_months / 12
        st.sidebar.write(f"**New Loan Term:** {new_loan_term_years:.1f} years ({new_loan_term_months:.0f} months)")
        st.sidebar.write(f"**Time Saved:** {loan_term_years - new_loan_term_years:.1f} years")
    else:
        st.sidebar.warning("Additional payment must be greater than interest-only payment")
else:
    new_loan_term_months = loan_term_months
    new_loan_term_years = loan_term_years

# Closing Costs
st.sidebar.subheader("Closing Costs")
closing_costs = st.sidebar.number_input("Total Closing Costs ($)", 0, 100000, 8236, 100)

# --- Income Analysis ---
st.sidebar.header("Income Analysis")
monthly_rent = st.sidebar.number_input("Monthly Rent ($)", 0, 50000, 2495, 1)
rental_growth_rate = st.sidebar.number_input("Annual Rental Growth Rate (%)", 0.0, 20.0, 3.0, 0.1) / 100

# --- Expense Analysis ---
st.sidebar.header("Operating Expenses")

# Insurance
monthly_fire_insurance = st.sidebar.number_input("Fire Insurance ($/month)", 0, 5000, 150, 1)
monthly_flood_insurance = st.sidebar.number_input("Flood Insurance ($/month)", 0, 5000, 0, 1)
monthly_liability_insurance = st.sidebar.number_input("Liability Insurance ($/month)", 0, 5000, 0, 1)
monthly_mortgage_insurance = st.sidebar.number_input("Mortgage Insurance ($/month)", 0, 5000, 237, 1)

# Property Taxes
monthly_property_taxes = st.sidebar.number_input("Property Taxes ($/month)", 0, 5000, 329, 1)

# Maintenance
monthly_repairs_maintenance = st.sidebar.number_input("Repairs & Maintenance ($/month)", 0, 5000, 359, 1)
monthly_janitorial = st.sidebar.number_input("Janitorial Service ($/month)", 0, 5000, 0, 1)
monthly_landscaping = st.sidebar.number_input("Landscaping ($/month)", 0, 5000, 0, 1)
monthly_pool_service = st.sidebar.number_input("Pool & Spa Service ($/month)", 0, 5000, 0, 1)

# Utilities
monthly_electricity = st.sidebar.number_input("Electricity ($/month)", 0, 5000, 0, 1)
monthly_gas = st.sidebar.number_input("Gas ($/month)", 0, 5000, 0, 1)
monthly_sewer_water = st.sidebar.number_input("Sewer & Water ($/month)", 0, 5000, 30, 1)
monthly_trash = st.sidebar.number_input("Trash ($/month)", 0, 5000, 30, 1)
monthly_telephone = st.sidebar.number_input("Telephone ($/month)", 0, 5000, 0, 1)

# Other Expenses
monthly_hoa = st.sidebar.number_input("HOA Fees ($/month)", 0, 5000, 0, 1)
monthly_management = st.sidebar.number_input("Property Management ($/month)", 0, 5000, 0, 1)
monthly_vacancy = st.sidebar.number_input("Vacancy Allowance ($/month)", 0, 5000, 0, 1)

# --- Tax Parameters ---
st.sidebar.header("Tax Parameters")
federal_tax_rate = st.sidebar.number_input("Federal Tax Rate (%)", 0.0, 50.0, 0.0, 0.1) / 100
state_tax_rate = st.sidebar.number_input("State Tax Rate (%)", 0.0, 20.0, 0.0, 0.1) / 100
total_tax_rate = federal_tax_rate + state_tax_rate

# --- Growth Assumptions ---
st.sidebar.header("Growth Assumptions")
property_appreciation_rate = st.sidebar.number_input("Property Appreciation Rate (%)", 0.0, 20.0, 3.0, 0.1) / 100
expense_inflation_rate = st.sidebar.number_input("Expense Inflation Rate (%)", 0.0, 20.0, 3.0, 0.1) / 100

# --- Analysis Period ---
analysis_years = st.sidebar.number_input("Analysis Period (Years)", 1, 30, 15, 1)

# --- Calculations ---
def calculate_remaining_loan_balance(principal, rate, total_payments, payments_made):
    """Calculate remaining loan balance after n payments"""
    if rate == 0:
        return max(principal - (principal / total_payments) * payments_made, 0)
    r = rate
    n = total_payments
    p = payments_made
    return principal * (((1 + r) ** n - (1 + r) ** p) / ((1 + r) ** n - 1))

def calculate_real_estate_analysis():
    """Calculate comprehensive real estate analysis"""
    results = []
    
    current_property_value = purchase_price
    current_monthly_rent = monthly_rent
    
    # Calculate total monthly expenses
    total_monthly_expenses = (
        monthly_mortgage + monthly_fire_insurance + monthly_flood_insurance + 
        monthly_liability_insurance + monthly_mortgage_insurance + monthly_property_taxes +
        monthly_repairs_maintenance + monthly_janitorial + monthly_landscaping + 
        monthly_pool_service + monthly_electricity + monthly_gas + monthly_sewer_water +
        monthly_trash + monthly_telephone + monthly_hoa + monthly_management + monthly_vacancy
    )
    
    for year in range(1, analysis_years + 1):
        # Property appreciation
        current_property_value *= (1 + property_appreciation_rate)
        
        # Rental growth
        current_monthly_rent *= (1 + rental_growth_rate)
        annual_rent = current_monthly_rent * 12
        
        # Loan balance
        payments_made = year * 12
        current_loan_balance = calculate_remaining_loan_balance(
            loan_amount, monthly_rate, loan_term_months, payments_made
        )
        
        # Equity calculation
        current_equity = current_property_value - current_loan_balance
        equity_percentage = (current_equity / current_property_value) * 100 if current_property_value > 0 else 0
        
        # PMI removal when equity reaches 20%
        # PMI is only applicable when loan-to-value ratio is > 80% (equity < 20%)
        # AND when there's still a loan balance
        if equity_percentage >= 20 or current_loan_balance == 0:
            current_monthly_pmi = 0
        else:
            current_monthly_pmi = monthly_mortgage_insurance
        
        # Monthly expenses with inflation (excluding PMI which is handled separately)
        # Only include mortgage payment if there's still a loan balance
        current_monthly_mortgage = monthly_mortgage if current_loan_balance > 0 else 0
        
        base_monthly_expenses = (
            current_monthly_mortgage + monthly_fire_insurance + monthly_flood_insurance + 
            monthly_liability_insurance + monthly_property_taxes +
            monthly_repairs_maintenance + monthly_janitorial + monthly_landscaping + 
            monthly_pool_service + monthly_electricity + monthly_gas + monthly_sewer_water +
            monthly_trash + monthly_telephone + monthly_hoa + monthly_management + monthly_vacancy
        )
        inflated_monthly_expenses = base_monthly_expenses * (1 + expense_inflation_rate) ** (year - 1) + current_monthly_pmi
        
        # Net operating income
        gross_operating_income = annual_rent
        net_operating_income = gross_operating_income - (inflated_monthly_expenses * 12)
        
        # Mortgage interest for tax deduction
        total_mortgage_interest = 0
        if current_loan_balance > 0:  # Only calculate interest if there's still a loan
            for month in range(12):
                month_balance = calculate_remaining_loan_balance(
                    loan_amount, monthly_rate, loan_term_months, (year-1)*12 + month
                )
                total_mortgage_interest += month_balance * monthly_rate
        
        # Depreciation
        annual_depreciation = purchase_price / 27.5  # Residential rental property
        
        # Taxable income
        # Calculate deductions properly (excluding mortgage payment from expenses for tax purposes)
        base_monthly_expenses_for_tax = (
            monthly_fire_insurance + monthly_flood_insurance + 
            monthly_liability_insurance + monthly_property_taxes +
            monthly_repairs_maintenance + monthly_janitorial + monthly_landscaping + 
            monthly_pool_service + monthly_electricity + monthly_gas + monthly_sewer_water +
            monthly_trash + monthly_telephone + monthly_hoa + monthly_management + monthly_vacancy
        )
        inflated_monthly_expenses_for_tax = base_monthly_expenses_for_tax * (1 + expense_inflation_rate) ** (year - 1) + current_monthly_pmi
        
        total_deductions = (inflated_monthly_expenses_for_tax * 12) + total_mortgage_interest + annual_depreciation
        taxable_income = gross_operating_income - total_deductions
        
        # Tax savings
        tax_savings = max(0, -taxable_income * total_tax_rate) if taxable_income < 0 else 0
        
        # Cash flow
        monthly_cash_flow = current_monthly_rent - inflated_monthly_expenses
        annual_cash_flow = monthly_cash_flow * 12 + tax_savings
        
        # Net profit/loss (includes depreciation and other non-cash items)
        # Net profit = Gross income - Operating expenses - Depreciation - Mortgage interest
        net_profit_loss = gross_operating_income - (inflated_monthly_expenses_for_tax * 12) - annual_depreciation - total_mortgage_interest
        
        # Cumulative cash flow
        if year == 1:
            cumulative_cash_flow = -down_payment - closing_costs + annual_cash_flow
        else:
            cumulative_cash_flow = results[-1]['cumulative_cash_flow'] + annual_cash_flow
        
        # Cash on cash return
        total_invested = down_payment + closing_costs
        cash_on_cash_return = (annual_cash_flow / total_invested) * 100 if total_invested > 0 else 0
        
        # Property sale analysis (if sold at end of year)
        sale_price = current_property_value
        sale_closing_costs = sale_price * 0.06  # 6% typical realtor fees
        net_sale_proceeds = sale_price - sale_closing_costs - current_loan_balance
        # Total profit = Sale proceeds + All cash flow received - Initial investment
        total_profit = net_sale_proceeds + cumulative_cash_flow - total_invested
        
        results.append({
            'year': year,
            'property_value': current_property_value,
            'monthly_rent': current_monthly_rent,
            'annual_rent': annual_rent,
            'loan_balance': current_loan_balance,
            'equity': current_equity,
            'equity_percentage': equity_percentage,
            'monthly_pmi': current_monthly_pmi,
            'monthly_expenses': inflated_monthly_expenses,
            'annual_expenses': inflated_monthly_expenses * 12,
            'net_operating_income': net_operating_income,
            'monthly_cash_flow': monthly_cash_flow,
            'annual_cash_flow': annual_cash_flow,
            'net_profit_loss': net_profit_loss,
            'cumulative_cash_flow': cumulative_cash_flow,
            'cash_on_cash_return': cash_on_cash_return,
            'tax_savings': tax_savings,
            'sale_price': sale_price,
            'net_sale_proceeds': net_sale_proceeds,
            'total_profit': total_profit,
            'total_roi': (total_profit / total_invested) * 100 if total_invested > 0 else 0
        })
    
    return results

# Calculate analysis
analysis_results = calculate_real_estate_analysis()

# --- Display Results ---
st.header("Investment Summary")

# First year summary
first_year = analysis_results[0]
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Initial Investment", f"${down_payment + closing_costs:,.0f}")
    st.metric("Monthly Cash Flow", f"${first_year['monthly_cash_flow']:,.0f}")

with col2:
    st.metric("Cash on Cash Return", f"{first_year['cash_on_cash_return']:.1f}%")
    st.metric("Net Profit/Loss (Year 1)", f"${first_year['net_profit_loss']:,.0f}")

with col3:
    st.metric("Annual Cash Flow", f"${first_year['annual_cash_flow']:,.0f}")
    st.metric("Tax Savings (Year 1)", f"${first_year['tax_savings']:,.0f}")

with col4:
    st.metric("Total ROI (15 years)", f"{analysis_results[-1]['total_roi']:.1f}%")
    st.metric("Total Profit (15 years)", f"${analysis_results[-1]['total_profit']:,.0f}")

# --- Detailed Analysis Table ---
st.header("Year-by-Year Analysis")

# Create DataFrame for display
df = pd.DataFrame(analysis_results)
display_df = df[['year', 'property_value', 'monthly_rent', 'equity', 'equity_percentage', 
                 'monthly_pmi', 'monthly_cash_flow', 'annual_cash_flow', 'net_profit_loss', 'tax_savings', 'cumulative_cash_flow', 
                 'cash_on_cash_return', 'total_roi']].copy()

# Format columns
display_df['property_value'] = display_df['property_value'].apply(lambda x: f"${x:,.0f}")
display_df['monthly_rent'] = display_df['monthly_rent'].apply(lambda x: f"${x:,.0f}")
display_df['equity'] = display_df['equity'].apply(lambda x: f"${x:,.0f}")
display_df['equity_percentage'] = display_df['equity_percentage'].apply(lambda x: f"{x:.1f}%")
display_df['monthly_pmi'] = display_df['monthly_pmi'].apply(lambda x: f"${x:,.0f}")
display_df['monthly_cash_flow'] = display_df['monthly_cash_flow'].apply(lambda x: f"${x:,.0f}")
display_df['annual_cash_flow'] = display_df['annual_cash_flow'].apply(lambda x: f"${x:,.0f}")
display_df['net_profit_loss'] = display_df['net_profit_loss'].apply(lambda x: f"${x:,.0f}")
display_df['tax_savings'] = display_df['tax_savings'].apply(lambda x: f"${x:,.0f}")
display_df['cumulative_cash_flow'] = display_df['cumulative_cash_flow'].apply(lambda x: f"${x:,.0f}")
display_df['cash_on_cash_return'] = display_df['cash_on_cash_return'].apply(lambda x: f"{x:.1f}%")
display_df['total_roi'] = display_df['total_roi'].apply(lambda x: f"{x:.1f}%")

display_df.columns = ['Year', 'Property Value', 'Monthly Rent', 'Equity', 'Equity %', 
                      'Monthly PMI', 'Monthly CF', 'Annual CF', 'Net P/L', 'Tax Savings', 'Cumulative CF', 'Cash on Cash %', 'Total ROI %']

st.dataframe(display_df, use_container_width=True)

# --- Charts ---
st.header("Investment Performance Charts")

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Chart 1: Property Value vs Equity
years = [r['year'] for r in analysis_results]
property_values = [r['property_value'] for r in analysis_results]
equity_values = [r['equity'] for r in analysis_results]
loan_balances = [r['loan_balance'] for r in analysis_results]

ax1.plot(years, property_values, label='Property Value', linewidth=2, color='blue')
ax1.plot(years, equity_values, label='Equity', linewidth=2, color='green')
ax1.plot(years, loan_balances, label='Loan Balance', linewidth=2, color='red')
ax1.set_title('Property Value, Equity, and Loan Balance Over Time', fontsize=14, fontweight='bold')
ax1.set_xlabel('Years')
ax1.set_ylabel('Amount ($)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Chart 2: Cash Flow Analysis
monthly_cash_flows = [r['monthly_cash_flow'] for r in analysis_results]
annual_cash_flows = [r['annual_cash_flow'] for r in analysis_results]
cumulative_cash_flows = [r['cumulative_cash_flow'] for r in analysis_results]

ax2.plot(years, monthly_cash_flows, label='Monthly Cash Flow', linewidth=2, color='orange')
ax2.plot(years, annual_cash_flows, label='Annual Cash Flow', linewidth=2, color='purple')
ax2.plot(years, cumulative_cash_flows, label='Cumulative Cash Flow', linewidth=2, color='brown')
ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.set_title('Cash Flow Analysis Over Time', fontsize=14, fontweight='bold')
ax2.set_xlabel('Years')
ax2.set_ylabel('Cash Flow ($)')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Chart 3: Returns Analysis
cash_on_cash_returns = [r['cash_on_cash_return'] for r in analysis_results]
total_rois = [r['total_roi'] for r in analysis_results]

ax3.plot(years, cash_on_cash_returns, label='Cash on Cash Return', linewidth=2, color='cyan')
ax3.plot(years, total_rois, label='Total ROI', linewidth=2, color='magenta')
ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax3.set_title('Return Metrics Over Time', fontsize=14, fontweight='bold')
ax3.set_xlabel('Years')
ax3.set_ylabel('Return (%)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Chart 4: PMI and Equity Analysis
monthly_pmis = [r['monthly_pmi'] for r in analysis_results]
equity_percentages = [r['equity_percentage'] for r in analysis_results]

# Create secondary y-axis for equity percentage
ax4_twin = ax4.twinx()

ax4.plot(years, monthly_pmis, label='Monthly PMI', linewidth=2, color='red', marker='o')
ax4_twin.plot(years, equity_percentages, label='Equity %', linewidth=2, color='blue', linestyle='--')

# Add horizontal line at 20% equity
ax4_twin.axhline(y=20, color='green', linestyle=':', alpha=0.7, label='20% Equity Threshold')

ax4.set_title('PMI and Equity Analysis Over Time', fontsize=14, fontweight='bold')
ax4.set_xlabel('Years')
ax4.set_ylabel('Monthly PMI ($)', color='red')
ax4_twin.set_ylabel('Equity Percentage (%)', color='blue')

# Combine legends
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax4.grid(True, alpha=0.3)
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax4_twin.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

plt.tight_layout()
st.pyplot(fig)

# --- Key Metrics Summary ---
st.header("Key Investment Metrics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Purchase Analysis")
    st.write(f"**Purchase Price:** ${purchase_price:,.0f}")
    st.write(f"**Down Payment:** ${down_payment:,.0f}")
    st.write(f"**Loan Amount:** ${loan_amount:,.0f}")
    st.write(f"**Closing Costs:** ${closing_costs:,.0f}")
    st.write(f"**Total Initial Investment:** ${down_payment + closing_costs:,.0f}")
    st.write(f"**Monthly Mortgage Payment:** ${monthly_mortgage:,.2f}")

with col2:
    st.subheader("First Year Performance")
    st.write(f"**Monthly Cash Flow:** ${first_year['monthly_cash_flow']:,.2f}")
    st.write(f"**Annual Cash Flow:** ${first_year['annual_cash_flow']:,.2f}")
    st.write(f"**Cash on Cash Return:** {first_year['cash_on_cash_return']:.1f}%")
    st.write(f"**Equity Percentage:** {first_year['equity_percentage']:.1f}%")
    st.write(f"**Net Operating Income:** ${first_year['net_operating_income']:,.2f}")

# --- PMI Analysis ---
st.header("PMI (Private Mortgage Insurance) Analysis")

# Find when PMI gets removed
pmi_removal_year = None
for result in analysis_results:
    if result['monthly_pmi'] == 0:
        pmi_removal_year = result['year']
        break

if pmi_removal_year:
    st.success(f"🏠 **PMI Removal:** Year {pmi_removal_year}")
    st.write(f"PMI will be removed when equity reaches 20% (Year {pmi_removal_year}).")
    
    # Calculate PMI savings
    total_pmi_paid = sum([r['monthly_pmi'] * 12 for r in analysis_results[:pmi_removal_year-1]])
    st.write(f"**Total PMI Paid:** ${total_pmi_paid:,.2f}")
    st.write(f"**Monthly PMI Savings After Removal:** ${monthly_mortgage_insurance:,.2f}")
else:
    st.warning("⚠️ **PMI Status:** PMI will not be removed within analysis period")
    st.write("Equity may not reach 20% within the current analysis period.")

# --- Tax Benefits Analysis ---
st.header("Tax Benefits Analysis")

# Calculate total tax savings over the analysis period
total_tax_savings = sum([r['tax_savings'] for r in analysis_results])
avg_annual_tax_savings = total_tax_savings / len(analysis_results)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Tax Savings", f"${total_tax_savings:,.0f}")
    
with col2:
    st.metric("Average Annual Tax Savings", f"${avg_annual_tax_savings:,.0f}")
    
with col3:
    st.metric("Tax Savings % of Total Investment", f"{(total_tax_savings / (down_payment + closing_costs)) * 100:.1f}%")

# Show tax savings trend
tax_savings_data = [r['tax_savings'] for r in analysis_results]
st.write("**Tax Savings Trend:**")
st.write(f"Tax savings are generated from deductions including mortgage interest, depreciation, and operating expenses.")
st.write(f"Total tax savings over {analysis_years} years: **${total_tax_savings:,.0f}**")

# --- Cash Flow vs Net Profit/Loss Analysis ---
st.header("Cash Flow vs Net Profit/Loss Analysis")

# Calculate totals
total_cash_flow = sum([r['annual_cash_flow'] for r in analysis_results])
total_net_profit_loss = sum([r['net_profit_loss'] for r in analysis_results])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cash Flow")
    st.write("**What it includes:**")
    st.write("• Rental income")
    st.write("• All operating expenses")
    st.write("• Mortgage payments")
    st.write("• Tax savings")
    st.write(f"**Total Cash Flow:** ${total_cash_flow:,.0f}")

with col2:
    st.subheader("Net Profit/Loss")
    st.write("**What it includes:**")
    st.write("• Rental income")
    st.write("• Operating expenses (excluding mortgage principal)")
    st.write("• Depreciation (non-cash expense)")
    st.write("• Mortgage interest only")
    st.write(f"**Total Net Profit/Loss:** ${total_net_profit_loss:,.0f}")

st.info("""
**Key Difference:** Cash flow shows actual money in/out, while net profit/loss is an accounting measure that includes 
non-cash items like depreciation. Net profit/loss is typically lower (or more negative) than cash flow because 
depreciation reduces taxable income but doesn't affect cash flow.
""")

# --- Break-even Analysis ---
st.header("Break-even Analysis")

# Find when cumulative cash flow becomes positive
break_even_year = None
for result in analysis_results:
    if result['cumulative_cash_flow'] >= 0:
        break_even_year = result['year']
        break

if break_even_year:
    st.success(f"💰 **Break-even Point:** {break_even_year} years")
    st.write(f"Your investment will start generating positive cumulative cash flow after {break_even_year} years.")
else:
    st.warning("⚠️ **Break-even Point:** Not reached within analysis period")
    st.write("The investment may not break even within the current analysis period.")

# --- Risk Analysis ---
st.header("Risk Analysis")

# Calculate key risk metrics
initial_investment = down_payment + closing_costs
max_negative_cash_flow = min([r['monthly_cash_flow'] for r in analysis_results])
avg_monthly_cash_flow = np.mean([r['monthly_cash_flow'] for r in analysis_results])
cash_flow_volatility = np.std([r['monthly_cash_flow'] for r in analysis_results])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Maximum Monthly Loss", f"${max_negative_cash_flow:,.0f}")
    
with col2:
    st.metric("Average Monthly Cash Flow", f"${avg_monthly_cash_flow:,.0f}")
    
with col3:
    st.metric("Cash Flow Volatility", f"${cash_flow_volatility:,.0f}")

# --- Recommendations ---
st.header("Investment Recommendations")

if first_year['cash_on_cash_return'] > 8:
    st.success("✅ **Strong Investment:** High cash-on-cash return indicates good income potential")
elif first_year['cash_on_cash_return'] > 5:
    st.info("📊 **Moderate Investment:** Reasonable returns with potential for appreciation")
else:
    st.warning("⚠️ **Consider Carefully:** Low initial returns, focus on long-term appreciation")

if break_even_year and break_even_year <= 5:
    st.success("✅ **Quick Break-even:** Investment recovers initial costs relatively quickly")
elif break_even_year and break_even_year <= 10:
    st.info("📊 **Moderate Break-even:** Reasonable time to recover investment")
else:
    st.warning("⚠️ **Long Break-even:** Consider if long-term appreciation justifies the wait")

st.caption("""
**Disclaimer:** This analysis is for educational purposes only. Actual results may vary based on market conditions, 
property performance, and other factors. Consult with financial and real estate professionals before making investment decisions.
""") 