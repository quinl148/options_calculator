# options_calculator

I built a dashboard that allows you to enter a stock ticker (has to exist in yahoo finance) and it provides the following information.

-Returns Chart (over any time period you choose)
-Implied Volatility over strike prices for calls and puts
-Options Chains for Calls and Puts (will adjust if you change expiration date input)

I also have dyanmic charts and data for long calls, long puts, short calls, short puts. 

You can adjust expiration date, strike price, and ending stock price and it will provide accurate real-time calculations for
  -payoff chart
  -Total Premium, Breakeven Price, Stock Return Needed to Profit, Option Return, Option Return Percentage

Finally, the Greeks are calcualted based on the expiration date, strike price, and interest rate. 

Check out my dashboard here: https://optionscalculator-o6lqumvnaydtfeffeejocm.streamlit.app/
