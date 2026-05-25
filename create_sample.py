import pandas as pd

data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Age': [25, 30, 35, 40],
    'Department': ['HR', 'Engineering', 'Marketing', 'Sales'],
    'Salary': [50000, 80000, 60000, 70000]
}

df = pd.DataFrame(data)
df.to_excel('sample.xlsx', index=False)
print("sample.xlsx created successfully!")
