# TickWise - A trading journal

## An alternative journal software with statistical analysis

### Features Planned:
- Account management
	- [x] Balance
	- [x] Deposits
	- [x] Withdrawals
- Trade data (user added)
	- [x] Instrument
	- [x] Long/Short
	- [x] Entry
	- [x] Stop
	- [x] Target
	- [x] Exit
    - [x] Monetary profit
	- [x] Commissions
	- [x] Trigger timeframe
	- [x] Highest/lowest price (automate in future)
	- [x] Entry strategy
	- [x] Management strategy
    - [x] Hit original target checkbox
	- [x] Exit strategy
	- [x] Confluence factors
        - Trade has many re-defined confluence categories, eg which price action, is level visible on other timeframes
        - These confluence categories have pre-defined options eg for category 'price action', options could be pinbar, engulfing etc.
	- [x] Entry grade
	- [x] Stop grade
	- [x] Target grade
	- [x] Management grade
- Trade derived data
	- [x] Planned R
	- [x] Actual R
	- [ ] MAE / MFE
- Display
    - [x] List of trades
    - Charts
        - [x] Total R by day
        - [ ] Total R by week
        - [ ] Total R by instrument
        - [ ] MAE + MFE per trade
        - [ ] Cumulative P&L + underwater chart
        - [ ] Management chart
        - [ ] Holding time vs Return
        - [ ] Risk reward frequency histogram
        - [ ] Simulator
    - Summary data
        - [x] Number / % winners / losers
        - [x] Expectancy
        - [x] Avg planned R
        - [x] Avg winner / loser
        - [x] Current win / lose streak
        - [x] Number / % winning days
        - [ ] Max consecutive wins/losses
        - [ ] Avg MAE / MFE


### How to run 

```bash
uv sync --frozen

python manage.py migrate
python manage.py runserver
```


### Technology:
- Django
- Django Ninja - for REST API endpoints
- SQLite3 - development database
- pytest - testing (waiting on this feature)
- ruff - formatting
- pyright - static type checking
- pre-commit - precommit hooks
- uv - package management