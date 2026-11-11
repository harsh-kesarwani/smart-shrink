# Smart Shrink

Steps to run the UI and script:
1. `git clone https://github.com/harsh-kesarwani/smart-shrink.git`
2. `cd smart-shrink`
3. `python3 -m venv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. `python manage.py runserver` and access UI via http://127.0.0.1:8000/services/
7. Refresh data using `cd scripts` and then run `python refresh_data.py`
8. Once the data refresh is complete, the results will be stored in results.json file in the repository. Refresh the UI to show the latest data