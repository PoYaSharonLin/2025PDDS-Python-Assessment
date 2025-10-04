# 2025 PDDS-Python-Assignment

This repo is used to evaluate the python code from the students. 

## File Structure 

```
.
├── README.md
├── output # the output folder to save the scores
├── pandas_src
│   └── studentID_pandas.py # implement your code here
├── python_list_src
│   └── studentID_python_list.py # implement your code here
├── requirements.txt
├── spec
│   ├── grade_pandas.py # grading script for pandas assignment
│   └── grade_python_list.py # grading script for python list assignment
```



## Run Tests 

### Set up virtual environment 

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run tests 

For python list assignment, run:
```bash
python3 spec/grade_python_list.py
```
For Pandas assignment, run:
```bash
python3 spec/grade_pandas.py
```

### View scores
The scores will be saved in `output` folder as CSV files.







