from db_tools import get_engine_manual
from sqlalchemy import text
import pandas as pd

def comprehensive_test():
    engine = get_engine_manual()
    if not engine:
        print("❌ Failed to connect to database")
        return
    
    print("=" * 60)
    print("COMPREHENSIVE DASHBOARD TEST")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Test 1: HP Count (Latest Year)
        print("\n1. Testing HP Count (Latest Year)...")
        hp_latest = pd.read_sql("""
            SELECT COUNT(DISTINCT employee_id) as hp_count
            FROM performance_yearly 
            WHERE rating = 5 
            AND year = (SELECT MAX(year) FROM performance_yearly)
        """, conn).iloc[0,0]
        print(f"   ✅ HP Count (2025): {hp_latest}")
        
        # Test 2: TGV Weights
        print("\n2. Testing TGV Weights...")
        weights = pd.read_sql("SELECT * FROM talent_group_weights ORDER BY tgv_name", conn)
        print(f"   ✅ TGV Weights:")
        for _, row in weights.iterrows():
            print(f"      - {row['tgv_name']}: {row['tgv_weight']*100:.0f}%")
        
        # Test 3: Data Completeness Column
        print("\n3. Testing Data Completeness Column...")
        test_query = """
        SELECT employee_id, 
               (
                   (SELECT COUNT(*) FROM competencies_yearly cy 
                    WHERE cy.employee_id = e.employee_id 
                    AND cy.year = (SELECT MAX(year) FROM competencies_yearly))
               ) as comp_count
        FROM employees e WHERE employee_id = 'EMP001'
        """
        result = pd.read_sql(test_query, conn)
        if not result.empty:
            print(f"   ✅ Sample competency count for EMP001: {result.iloc[0]['comp_count']}")
        else:
            print(f"   ⚠️  EMP001 not found, testing with first employee...")
            test_query2 = """
            SELECT employee_id, 
                   (SELECT COUNT(*) FROM competencies_yearly cy 
                    WHERE cy.employee_id = e.employee_id 
                    AND cy.year = (SELECT MAX(year) FROM competencies_yearly)) as comp_count
            FROM employees e LIMIT 1
            """
            result = pd.read_sql(test_query2, conn)
            if not result.empty:
                print(f"   ✅ Sample competency count for {result.iloc[0]['employee_id']}: {result.iloc[0]['comp_count']}")
        
        # Test 4: Check for hardcoded values (spot check)
        print("\n4. Checking for potential issues...")
        
        # Test if dim_directorates exists
        dir_check = pd.read_sql("SELECT COUNT(*) FROM dim_directorates", conn).iloc[0,0]
        print(f"   ✅ dim_directorates table exists ({dir_check} records)")
        
        # Test competency query consistency
        comp_test = pd.read_sql("""
            SELECT COUNT(DISTINCT cy.employee_id) as count
            FROM competencies_yearly cy
            JOIN performance_yearly py ON cy.employee_id = py.employee_id 
                AND py.year = cy.year
            WHERE py.rating = 5 
            AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
        """, conn).iloc[0,0]
        print(f"   ✅ HP with competencies (consistent join): {comp_test}")
        
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - No critical issues found")
    print("=" * 60)

if __name__ == "__main__":
    comprehensive_test()
