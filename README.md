# glassdoor-insights-dashboard

This repository contains the source code and supporting csv files for the Glassdoor Insights Dashboard which is an interactive data analytics tool for exploring workplace sentiment and EmpAt (Employer Attractiveness) dimensions using employee reviews.

The structure of the repository is as follows:

Source/

 │

 ├── dashboard.py          # Main Dash dashboard application to be run

 ├── analysis.py           # Scripts for data analysis

 ├── proc_dataset.py       # Data pre-processing and cleaning scripts

 ├── Bert_EmpAtModel.ipynb # Jupyter notebook for fine-tuning and using BERT

 ├── requirements.txt      # All libraries used 

 │

 └── CSV/
    ├── [various CSV files used by the app excluding df_reviews.csv]
    

How to Use:
1. Download the entire Source Folder from this repository, including all its contents and the nested CSV folder.
2. Download the main dataset, df_reviews.csv, which is not included in the repository due to its size.
Download df_reviews.csv here: https://drive.google.com/file/d/142TTxN-Se3Jc7_HdqAhAafwgeowQJ-yz/view?usp=drive_link
3. After downloading, save df_reviews.csv inside the CSV folder in Source directory
4. Open Command Prompt
5. Navigate to the Source directory
6. Install the required Python packages using: pip install -r requirements.txt
7. Run: python dashboard.py
8. Click the dashboard link in command prompt to open in browser.

