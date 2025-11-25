import pandas as pd
from db_tools import get_engine_manual
from sqlalchemy import text

def debug_hp():
    engine = get_engine_manual()
    if engine:
        with engine.connect() as conn:
            # 1. Total employees
            total = pd.read_sql("SELECT COUNT(DISTINCT employee_id) FROM employees", conn).iloc[0,0]
            print(f"Total Employees: {total}")

            # 2. HP (Any Year) - Current Dashboard Logic
            hp_any = pd.read_sql("SELECT COUNT(DISTINCT employee_id) FROM performance_yearly WHERE rating = 5", conn).iloc[0,0]
            print(f"HP (Any Year): {hp_any} ({hp_any/total:.1%})")

            # 3. HP (Latest Year) - Likely Report Logic
            hp_latest = pd.read_sql("""
                SELECT COUNT(DISTINCT employee_id) 
                FROM performance_yearly 
                WHERE rating = 5 
                AND year = (SELECT MAX(year) FROM performance_yearly)
            """, conn).iloc[0,0]
            print(f"HP (Latest Year): {hp_latest} ({hp_latest/total:.1%})")

            # 4. Check what year is "Latest"
            max_year = pd.read_sql("SELECT MAX(year) FROM performance_yearly", conn).iloc[0,0]
            print(f"Latest Year: {max_year}")

if __name__ == "__main__":
    debug_hp()
