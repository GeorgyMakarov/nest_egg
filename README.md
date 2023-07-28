# Monte Carlo Simulation of Retirement Savings

## Project summary

The objective of this repository is to provide a set of two tools that help a
person to plan short-term investment and long-term retirement plan using Monte
Carlo simulation. The tool for the short-term investment evaluation estimates
the probability of pulling out of investment with less money than initially put
into stocks. The tool for the long-term retirement planning approximates the odds
of running out of money in retirement.

Both simulations are as simple as possible and focus on things that a person
can control: retirement age, asset allocation, savings, expenses, pull out of
investment. The tools use historical returns to be able to capture the true
measured duration of good times and bad times. The historical period starts in
2002 and is rolling if a person runs the script as a  **cron job** daily or adds
up the last available day. The usage of long period allows a simulation to
catch **black swan** events and use them in the estimation of possible futures.

[Retirement simulation](https://github.com/GeorgyMakarov/nest_egg/blob/main/nest_egg_script.py)  
[Short-term investment](https://github.com/GeorgyMakarov/nest_egg/blob/main/etf_script.py)

## Sources

[Impractical Python Projects]()  
[Automating Google Colab](https://www.linkedin.com/pulse/automating-tasks-google-colab-step-by-step-guide-using-nick-gupta/)  
[Monte Carlo Method](https://en.wikipedia.org/wiki/Monte_Carlo_method)  