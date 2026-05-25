import pandas as pd

columns = [
    "N°Fact", "Rep", "Date", "Reçu", "Libelles", 
    "Versement", "Débours", "Honoraires", "T.V.A", "Honors/H.T"
]

# Create an empty dataframe with these columns and some empty rows
df = pd.DataFrame(columns=columns)
df.loc[0] = ["" for _ in range(10)]
df.loc[1] = ["" for _ in range(10)]
df.loc[2] = ["" for _ in range(10)]
df.loc[3] = ["" for _ in range(10)]
df.loc[4] = ["" for _ in range(10)]

df.to_excel("default_table.xlsx", index=False)
print("default_table.xlsx created with the specific structure!")
