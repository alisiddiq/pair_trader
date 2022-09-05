# Pair Trader

This is a webapp that allows the user to choose between 2 indices [SP 500, NASDAQ 100] and then run multiple pair trading strategies based on different scores:


- MDM: Select pairs where the sum of squared distances between cumulative returns of two stocks is the minimum 
- MFR:  Select pairs with minimum market factor ratio, an indicator that is the ratio of market betas of the two stocks
- G: Select pairs with minimum sum of p-value of 2 Granger-Causality tests. The test determines whether price of one stock is useful in predicting the price of another

Pairs are chosen in the training duration, and then the strategy is tested in the test period. The user has control over the entry and exit thresholds used for the strategies

## Start up

The initial start takes a long time since it needs to generate all the pairs and their respective metrics. 


# Run the Webapp

1. Make sure the DB is up and running and has been updated with the price data. (The data_feeds repo)
2. Edit the `db_conn_details.json` file with the DB connection and credential details 

### Via Docker 
Run the command

`docker-compose up`
    
This will spin up a server on port 8091

### Manually

1. Make sure all requirements are installed in a fresh env
2. From the root, run the command 

`gunicorn -b 0.0.0.0:8091 webapp.start_app:server -k gevent --timeout 600 --workers 4`




