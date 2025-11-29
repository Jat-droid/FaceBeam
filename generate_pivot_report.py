import sqlite3
from datetime import datetime
import csv

DB_NAME = 'facebeam.db'

def generate_pivot_report(report_date_str):
    """
    Generates a pivot-table-style CSV report with students as rows
    and subjects as columns for a specific date.
    """
    
    try:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        day_of_week = report_date.weekday() # Monday is 0, Sunday is 6
    except ValueError:
        print("❌ Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    print(f"Generating pivot report for {report_date_str}...")
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()

    try:
        # 1. Get all registered students (these will be our rows)
        cursor.execute("SELECT name FROM students ORDER BY name")
        all_students = [row['name'] for row in cursor.fetchall()]
        if not all_students:
            print("⚠️ Warning: No students found in the database.")
            return

        # 2. Get all subjects scheduled for that day (these will be our columns)
        query_schedule = """
            SELECT s.id as subject_id, s.name as subject_name 
            FROM timetable t 
            JOIN subjects s ON t.subject_id = s.id 
            WHERE t.day_of_week = ?
            ORDER BY t.start_time
        """
        cursor.execute(query_schedule, (day_of_week,))
        scheduled_subjects = cursor.fetchall() 
        
        if not scheduled_subjects:
            print(f"ℹ️ No classes were scheduled on {report_date_str} (Day {day_of_week}).")
            return

        # 3. Get all attendance records for the specified date
        query_attendance = "SELECT name, subject_id FROM attendance WHERE date(timestamp) = ?"
        cursor.execute(query_attendance, (report_date_str,))
        present_records = cursor.fetchall()
        
        # Create a set for quick lookup: {(student_name, subject_id)}
        present_set = {(rec['name'], rec['subject_id']) for rec in present_records}

        # 4. Prepare data for the CSV
        final_report_data = []
        
        # First, create the header row
        header = ['Student Name'] + [s['subject_name'] for s in scheduled_subjects]
        
        # Now, create one data row for each student
        for student_name in all_students:
            row_data = {'Student Name': student_name}
            for subject in scheduled_subjects:
                subject_id = subject['subject_id']
                subject_name = subject['subject_name']
                
                # Check if the student was present for this subject
                if (student_name, subject_id) in present_set:
                    row_data[subject_name] = "Present"
                else:
                    row_data[subject_name] = "Absent"
            
            final_report_data.append(row_data)

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return
    finally:
        conn.close()

    # 5. Write the final report to a CSV file
    output_filename = f'pivot_report_{report_date_str}.csv'
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(final_report_data)
        
        print(f"✅ Report '{output_filename}' generated successfully!")
    except IOError as e:
        print(f"❌ Error writing CSV file: {e}")


if __name__ == '__main__':
    date_input = input("Enter the date for the pivot report (YYYY-MM-DD): ")
    generate_pivot_report(date_input)