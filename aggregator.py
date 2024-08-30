import sqlite3

conn = sqlite3.connect('sqlite.db')
cursor = conn.cursor()
query = """SELECT 
    name,
    code,
    SUM(CASE WHEN type = 'B' THEN trading_value ELSE 0 END) AS total_buy_value,
    SUM(CASE WHEN type = 'S' THEN trading_value ELSE 0 END) AS total_sell_value
FROM 
    Trades
WHERE
    DATE(date) BETWEEN DATE('now', '-1 month') AND DATE('now')
GROUP BY 
    code;"""

cursor.execute(query)
results = cursor.fetchall()

with open("output.txt", "w") as file:
    for row in results:
        total = row[2] + row[3]
        if total:
            buy_percentage = round((row[2] / total) * 100, 2)
            sell_percentage = round((row[3] / total) * 100, 2)
        else:
            buy_percentage = 0
            sell_percentage = 0

        print(f"{'Name:':<15} {row[0]}")
        print(f"{'Code:':<15} {row[1]}")
        print(f"{'Buy Percentage:':<15} {buy_percentage:.2f}%")
        print(f"{'Sell Percentage:':<15} {sell_percentage:.2f}%")
        print("-------------------------------------------------")

        file.write(f"Name: {row[0]}\n")
        file.write(f"Code: {row[1]}\n")
        file.write(f"Buy Percentage: {buy_percentage:.2f}%\n")
        file.write(f"Sell Percentage: {sell_percentage:.2f}%\n")
        file.write("-------------------------------------------------\n")