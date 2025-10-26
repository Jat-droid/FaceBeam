import sqlite3
from datetime import datetime
import csv

DB_NAME = 'facebeam.db'

def generate_daily_report(report_date_str):
    """Generates a CSV report of Present/Absent status for all students for a given date."""
    
    try:
        # Validate and parse the input date
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        day_of_week = report_date.weekday() # Monday is 0, Sunday is 6
    except ValueError:
        print("❌ Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    print(f"Generating attendance status report for {report_date_str}...")
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()

    try:
        # 1. Get all registered students
        cursor.execute("SELECT name FROM students ORDER BY name")
        all_students = [row['name'] for row in cursor.fetchall()]
        if not all_students:
            print("⚠️ Warning: No students found in the database.")
            return

        # 2. Get all subjects scheduled for that specific day of the week
        query_schedule = """
            SELECT s.id as subject_id, s.name as subject_name 
            FROM timetable t 
            JOIN subjects s ON t.subject_id = s.id 
            WHERE t.day_of_week = ?
        """
        cursor.execute(query_schedule, (day_of_week,))
        scheduled_subjects = cursor.fetchall()
        if not scheduled_subjects:
            print(f"ℹ️ No classes were scheduled on {report_date_str} (Day {day_of_week}).")
            return

        # 3. Get all actual attendance records for the specified date
        query_attendance = """
            SELECT name, subject_id 
            FROM attendance 
            WHERE date(timestamp) = ?
        """
        cursor.execute(query_attendance, (report_date_str,))
        present_records = cursor.fetchall()
        
        # Create a set for quick lookup: {(student_name, subject_id)}
        present_set = {(rec['name'], rec['subject_id']) for rec in present_records}

        final_report_data = []
        # 4. Determine status for each student for each scheduled class
        for subject in scheduled_subjects:
            subject_id = subject['subject_id']
            subject_name = subject['subject_name']
            
            for student_name in all_students:
                status = "Absent" # Assume absent by default
                
                # Check if the student was present for this specific subject on this date
                if (student_name, subject_id) in present_set:
                    status = "Present"
                
                # Add the record to our report list
                final_report_data.append({
                    'Student Name': student_name,
                    'Subject Name': subject_name,
                    'Date': report_date_str,
                    'Status': status
                })

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return
    finally:
        conn.close() # Ensure connection is closed even if errors occur

    # 5. Write the final report to a CSV file
    if not final_report_data:
        print("ℹ️ No report data generated (perhaps no students or schedule?).")
        return

    output_filename = f'status_report_{report_date_str}.csv'
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            # Define the order of columns
            fieldnames = ['Date', 'Subject Name', 'Student Name', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(final_report_data)
        
        print(f"✅ Report '{output_filename}' generated successfully!")
    except IOError as e:
        print(f"❌ Error writing CSV file: {e}")


if __name__ == '__main__':
    date_input = input("Enter the date for the report (YYYY-MM-DD): ")
    generate_daily_report(date_input)
