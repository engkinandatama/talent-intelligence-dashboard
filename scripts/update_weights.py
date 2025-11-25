from db_tools import get_engine_manual
from sqlalchemy import text
import pandas as pd

def update_weights():
    engine = get_engine_manual()
    if engine:
        updates = {
            'Competency': 0.50,
            'Workstyle': 0.25,
            'Cognitive': 0.10,
            'Strengths': 0.10,
            'Personality': 0.05
        }
        
        with engine.connect() as conn:
            print("Updating weights...")
            for name, weight in updates.items():
                print(f"Updating {name} to {weight}")
                conn.execute(
                    text("UPDATE public.talent_group_weights SET tgv_weight = :weight WHERE tgv_name = :name"),
                    {"weight": weight, "name": name}
                )
            conn.commit()
            
            print("\nVerification:")
            df = pd.read_sql("SELECT * FROM public.talent_group_weights", conn)
            print(df)

            print("\nChecking for directorate_id:")
            res = conn.execute(text("SELECT table_name FROM information_schema.columns WHERE column_name = 'directorate_id'"))
            found = False
            for row in res:
                print(f"Found in table: {row[0]}")
                found = True
            if not found:
                print("directorate_id not found in any table.")
                
            print("\nChecking for dim_directorates table:")
            res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'dim_directorates'"))
            for row in res:
                print(f"Table exists: {row[0]}")

if __name__ == "__main__":
    update_weights()
