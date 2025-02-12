import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import datetime
import scipy.stats as stats
import math

st.title("Stock Options Payoff Calculator")

# Sidebar Inputs
ticker = st.sidebar.text_input('Enter Ticker Symbol:')
start_date = st.sidebar.date_input('Start Date')
end_date = st.sidebar.date_input('End Date')
interest_rate = st.sidebar.number_input('Enter the Risk-Free Rate:', min_value=0.0, max_value=100.0, value=4.45)


# Ensure valid date selection
if start_date >= end_date:
    st.error("End date must be after start date")
else:
    try:
        # Download stock data
        data = yf.download(ticker, start=start_date, end=end_date)

        # Fetch company name
        ticker_obj = yf.Ticker(ticker)
        company_name = ticker_obj.info.get('longName', ticker)

        # Check if data is empty
        if data.empty:
            st.error("No data found. Check the ticker symbol and date range.")
        else:
            # Fix multi-index issue
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)  # Keep only first level of column names

            # Plot stock price data
            fig = px.line(
                data, x=data.index, y="Close", 
                title=f"{company_name} ({ticker}) - Stock Price Over Time",
                labels={"Close": "Stock Price (USD)", "index": "Date"}
            )
            st.plotly_chart(fig)

            # Implied Volatility Graph below price history
            options_chain = ticker_obj.option_chain(ticker_obj.options[0])  # Example for first expiration date
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=options_chain.calls['strike'], y=options_chain.calls['impliedVolatility'], mode='lines', name='Call Implied Volatility'))
            fig3.add_trace(go.Scatter(x=options_chain.puts['strike'], y=options_chain.puts['impliedVolatility'], mode='lines', name='Put Implied Volatility'))
            fig3.update_layout(title=f"Implied Volatility for {ticker}", xaxis_title="Strike Price", yaxis_title="Implied Volatility")
            st.plotly_chart(fig3)

            # Tabs for Calls and Puts
            tab1, tab2 = st.tabs(["Calls", "Puts"])

            # Calls Tab
            with tab1:
                st.subheader("Call Options Chain")
                st.dataframe(options_chain.calls)

            # Puts Tab
            with tab2:
                st.subheader("Put Options Chain")
                st.dataframe(options_chain.puts)

    except Exception as e:
        st.error(f"Error fetching data: {e}")

# Fetch stock data
stock_data = yf.download(ticker, start=start_date, end=end_date)

# Get expiration dates
ticker_obj = yf.Ticker(ticker)
expiration_dates = ticker_obj.options
selected_expiration = st.sidebar.selectbox('Select Expiration Date', expiration_dates)
options_chain = ticker_obj.option_chain(selected_expiration)

# Fetch current stock price
current_stock_price = round(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1], 2)
rounded_stock_price = round(current_stock_price / 5) * 5
stock_input = st.sidebar.number_input("Enter Stock Price", value=rounded_stock_price, step=5)
strike_input = st.sidebar.number_input("Enter Strike Price", value=rounded_stock_price, step=5)

# Get the call and put premiums based on the strike price
call_options = options_chain.calls[options_chain.calls['strike'] == strike_input]
if not call_options.empty:
    # Premium paid (Ask) for call option
    call_premium_paid = call_options['ask'].values[0]
    # Premium received (Bid) for call option
    call_premium_received = call_options['bid'].values[0]
else:
    st.warning(f"No call option found for strike price {strike_input}")
    call_premium_paid = 0 
    call_premium_received = 0

put_options = options_chain.puts[options_chain.puts['strike'] == strike_input]
if not put_options.empty:
    # Premium paid (Ask) for put option
    put_premium_paid = put_options['ask'].values[0]
    # Premium received (Bid) for put option
    put_premium_received = put_options['bid'].values[0]
else:
    st.warning(f"No put option found for strike price {strike_input}")
    put_premium_paid = 0 
    put_premium_received = 0


long_call, long_put, short_call, short_put = st.tabs(["Long Call", "Long Put", "Short Call", "Short Put"])

# Long Call Section
with long_call:
    st.subheader("Long Call")

    lc_payoff = np.maximum(stock_input - strike_input, 0) - call_premium_paid
    lc_contract_payoff = lc_payoff * 100 
    total_call_premium_paid = call_premium_paid * 100
    stock_return = (stock_input - current_stock_price)/ current_stock_price * 100
    lc_option_return = (((np.maximum((stock_input - strike_input) * 100, 0) - total_call_premium_paid) / total_call_premium_paid)  ) *100 
    lc_price_needed = strike_input + call_premium_paid
    lc_stock_return_needed = (((lc_price_needed - current_stock_price)/current_stock_price) * 100)

    #graph inputs
    stock_prices = np.arange(stock_input * 0.5, stock_input * 1.5, 1)  # Range from 50% to 150% of current stock price
    lc_payoffs = np.maximum(stock_prices - strike_input, 0) - call_premium_paid  # Payoff calculation

    fig_payoff = go.Figure()
    fig_payoff.add_trace(go.Scatter(x=stock_prices, y=lc_payoffs, mode='lines', name='Long Call Payoff'))
    fig_payoff.update_layout(
        title="Long Call Payoff",
        xaxis_title="Stock Price",
        yaxis_title="Payoff ($)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        hovermode="x"
    )
    st.plotly_chart(fig_payoff)

    # Define color based on stock_return value
    stock_return_color = "green" if stock_return > 0 else "red"
    lc_contract_payoff_color = "green" if lc_contract_payoff > 0 else "red"
    lc_option_return_color = "green" if lc_option_return > 0 else "red"
    
    st.write(f"Current Stock Price: {current_stock_price}")
    st.write(f"Total Premium: {total_call_premium_paid:.2f}")
    st.write(f"Breakeven Price: {lc_price_needed:.2f}")
    st.write(f"Stock Return Needed for Profit: {lc_stock_return_needed:.2f}%")
    st.markdown(f'Stock Return: <span style="color:{stock_return_color}; font-weight:bold;">{stock_return:.2f}%</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return: <span style="color:{lc_contract_payoff_color}; font-weight:bold;">{lc_contract_payoff:.2f}</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return Percentage: <span style="color:{lc_option_return_color}; font-weight:bold;">{lc_option_return:.2f}%</span>', unsafe_allow_html=True)




# Long Put Section
with long_put:
    st.header('Long Put')

    lp_payoff = np.maximum(strike_input - stock_input, 0) - put_premium_paid
    lp_contract_payoff = lp_payoff * 100 
    total_put_premium_paid = put_premium_paid * 100
    stock_return = (stock_input - current_stock_price)/ current_stock_price
    lp_option_return = ((np.maximum((strike_input - stock_input) * 100, 0) - total_put_premium_paid) / total_put_premium_paid )* 100
    lp_price_needed = strike_input - put_premium_paid
    lp_stock_return_needed = ((lp_price_needed - current_stock_price)/current_stock_price * 100)

     #graph inputs
    stock_prices = np.arange(stock_input * 0.5, stock_input * 1.5, 1)  # Range from 50% to 150% of current stock price
    lp_payoffs = np.maximum(strike_input - stock_prices, 0) - put_premium_paid  # Payoff calculation

    fig_payoff = go.Figure()
    fig_payoff.add_trace(go.Scatter(x=stock_prices, y=lp_payoffs, mode='lines', name='Long Put Payoff'))
    fig_payoff.update_layout(
        title="Long Put Payoff",
        xaxis_title="Stock Price",
        yaxis_title="Payoff ($)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        hovermode="x"
    )
    st.plotly_chart(fig_payoff)


    # Define color based on stock_return value
    stock_return_color = "green" if stock_return > 0 else "red"
    lp_contract_payoff_color = "green" if lp_contract_payoff > 0 else "red"
    lp_option_return_color = "green" if lp_option_return > 0 else "red"

    st.write(f"Current Stock Price: {current_stock_price}")
    st.write(f"Total Premium: {total_put_premium_paid:.2f}")
    st.write(f"Breakeven Price: {lp_price_needed:.2f}")
    st.write(f"Stock Return Needed for Profit: {lp_stock_return_needed:.2f}%")
    st.markdown(f'Stock Return: <span style="color:{stock_return_color}; font-weight:bold;">{stock_return:.2f}%</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return: <span style="color:{lp_contract_payoff_color}; font-weight:bold;">{lp_contract_payoff:.2f}</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return Percentage: <span style="color:{lp_option_return_color}; font-weight:bold;">{lp_option_return:.2f}%</span>', unsafe_allow_html=True)

# Short Call Section
with short_call:
    st.subheader("Short Call")

    sc_payoff = call_premium_received - np.maximum(stock_input - strike_input, 0)
    sc_contract_payoff = sc_payoff * 100 
    total_call_premium_received = call_premium_received * 100
    stock_return = (stock_input - current_stock_price) / current_stock_price * 100
    sc_option_return = (total_call_premium_received - np.maximum((stock_input - strike_input) * 100, 0)) / total_call_premium_received * 100
    sc_price_needed = strike_input + call_premium_received
    sc_stock_return_needed = ((sc_price_needed - current_stock_price) / current_stock_price * 100)

    # Graph inputs
    stock_prices = np.arange(stock_input * 0.5, stock_input * 1.5, 1)  # Range from 50% to 150% of current stock price
    sc_payoffs = call_premium_received - np.maximum(stock_prices - strike_input, 0)  # Payoff calculation

    fig_payoff = go.Figure()
    fig_payoff.add_trace(go.Scatter(x=stock_prices, y=sc_payoffs, mode='lines', name='Short Call Payoff'))
    fig_payoff.update_layout(
        title="Short Call Payoff",
        xaxis_title="Stock Price",
        yaxis_title="Payoff ($)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        hovermode="x"
    )
    st.plotly_chart(fig_payoff)

    # Define color based on stock_return value
    stock_return_color = "green" if stock_return > 0 else "red"
    sc_contract_payoff_color = "green" if sc_contract_payoff > 0 else "red"
    sc_option_return_color = "green" if sc_option_return > 0 else "red"

    st.write(f"Current Stock Price: {current_stock_price}")
    st.write(f"Total Premium: {total_call_premium_received:.2f}")
    st.write(f"Breakeven Price: {sc_price_needed:.2f}")
    st.write(f"Stock Return Needed for Profit: {sc_stock_return_needed:.2f}%")
    st.markdown(f'Stock Return: <span style="color:{stock_return_color}; font-weight:bold;">{stock_return:.2f}%</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return: <span style="color:{sc_contract_payoff_color}; font-weight:bold;">{sc_contract_payoff:.2f}</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return Percentage: <span style="color:{sc_option_return_color}; font-weight:bold;">{sc_option_return:.2f}%</span>', unsafe_allow_html=True)

#Short Put

with short_put:
    st.header('Short Put')

    sp_payoff = put_premium_received - np.maximum(strike_input - stock_input, 0)
    sp_contract_payoff = sp_payoff * 100 
    total_put_premium_received = put_premium_received * 100
    stock_return = (stock_input - current_stock_price)/ current_stock_price
    sp_option_return = ((put_premium_received - np.maximum(strike_input - stock_input, 0)) * 100) / total_put_premium_received * 100
    sp_price_needed = strike_input - put_premium_received
    sp_stock_return_needed = ((sp_price_needed - current_stock_price) / current_stock_price) * 100

    stock_prices = np.arange(stock_input * 0.5, stock_input * 1.5, 1)  # Range from 50% to 150% of current stock price
    sp_payoffs = put_premium_received - np.maximum(strike_input - stock_prices, 0)

    fig_payoff = go.Figure()
    fig_payoff.add_trace(go.Scatter(x=stock_prices, y=sp_payoffs, mode='lines', name='Short Put Payoff'))
    fig_payoff.update_layout(
        title="Short Put Payoff",
        xaxis_title="Stock Price",
        yaxis_title="Payoff ($)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        hovermode="x"
    )
    st.plotly_chart(fig_payoff)

    # Define color based on stock_return value
    stock_return_color = "green" if stock_return > 0 else "red"
    sp_contract_payoff_color = "green" if sp_contract_payoff > 0 else "red"
    sp_option_return_color = "green" if sp_option_return > 0 else "red"

    st.write(f"Current Stock Price: {current_stock_price}")
    st.write(f"Total Premium: {total_put_premium_received:.2f}")
    st.write(f"Breakeven Price: {sp_price_needed:.2f}")
    st.write(f"Stock Return Needed for Profit: {sp_stock_return_needed:.2f}%")
    st.markdown(f'Stock Return: <span style="color:{stock_return_color}; font-weight:bold;">{stock_return:.2f}%</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return: <span style="color:{sp_contract_payoff_color}; font-weight:bold;">{sp_contract_payoff:.2f}</span>', unsafe_allow_html=True)
    st.markdown(f'Option Return Percentage: <span style="color:{sp_option_return_color}; font-weight:bold;">{sp_option_return:.2f}%</span>', unsafe_allow_html=True)


# Option Greeks Calculation
st.subheader("Greeks")


end_date = datetime.datetime.strptime(selected_expiration, "%Y-%m-%d").date()
current_date = datetime.date.today()
time_to_expiration_days = (end_date - current_date).days 
T = time_to_expiration_days / 365
S = current_stock_price
K = strike_input
r = interest_rate / 100
v = options_chain.calls[options_chain.calls['strike'] == strike_input]['impliedVolatility'].values[0]

d1 = (np.log(S / K) + (r + (v**2) / 2) * T) / (v * np.sqrt(T))
d2 = d1 - v * np.sqrt(T)

N_prime_d1 = stats.norm.pdf(d1)
N_d1 = stats.norm.cdf(d1)
N_d2 = stats.norm.cdf(d2)
put_delta = N_d1 - 1 

theta_call = (-S * v * N_prime_d1 / (2 * math.sqrt(T))) - (r * K * math.exp(-r * T) * N_d2)
theta_put = (-S * v * N_prime_d1 / (2 * math.sqrt(T))) + (r * K * math.exp(-r * T) * stats.norm.cdf(-d2))

gamma = stats.norm.pdf(d1) / (S * v * math.sqrt(T))
vega = S * math.sqrt(T) * stats.norm.pdf(d1)

# Call and Put Option Rho
rho_call = T * S * np.exp(-r * T) * N_d2
rho_put = -T * S * np.exp(-r * T) * N_d2

st.write(f"Call Option Theta: {theta_call:.2f}")
st.write(f"Put Option Theta: {theta_put:.2f}")

st.write(f"Call Option Delta: {N_d1:.2f}")
st.write(f"Put Option Delta: {put_delta:.2f}")

st.write(f"Option Gamma: {gamma:.2f}")
st.write(f"Option Vega: {vega:.2f}")

st.write(f"Call Option Rho: {rho_call:.2f}")
st.write(f"Put Option Rho: {rho_put:.2f}")


