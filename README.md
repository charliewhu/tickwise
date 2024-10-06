# TickWise - A trading journal

## An alternative journal software with statistical analysis

### Features Planned:
- Trade data (user added)
	- [x] Instrument
	- [x] Long/Short
	- [x] Entry
	- [x] Stop
	- [x] Target
	- [x] Exit
	- [x] Trigger timeframe
	- [] Highest/lowest price (automate in future)
	- [] Entry strategy
	- [] Management strategy
	- [] Exit strategy
	- [] Confluence factor
	- [x] Entry grade
	- [] Stop grade
	- [] Target grade
	- [x] Management grade
- Trade derived data
	- [x] Planned R
	- [x] Actual R
	- [] MAE / MFE
- Summary data
	- [x] Number / % winners / losers
	- [x] Expectancy
	- [x] Avg winner / loser
	- [x] Current win / lose streak
	- [x] Number / % winning days
	- [] Avg MAE / MFE


### How to run 

```bash
uv sync --frozen

nanodjango run main.py
```


### Technology:
- Django with Nanodjango - enabling a rapid prototype
- Django Ninja - for REST API endpoints
- SQLite3 - development database
- pytest - testing (waiting on this feature)
- ruff - formatting
- pyright - static type checking
- pre-commit - precommit hooks
- uv - package management