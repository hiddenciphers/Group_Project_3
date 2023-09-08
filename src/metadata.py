# Imports
import json
import requests

# Function to construct metadata
def create_metadata(certificate_id, course_title, course_fee, instructor_address, student_name, student_address, enrollment_date, exam_status, completion_date):
    metadata = {
        'certificate_id': certificate_id,
        'course_title': course_title,
        'course_fee': course_fee,
        'instructor_address': instructor_address,
        'student_name': student_name,
        'student_address': student_address,
        'enrollment_date': enrollment_date,
        'exam_status': exam_status,
        'completion_date': completion_date
    }
    return json.dumps(metadata)

# Function to pin to ipfs
def pin_to_ipfs(file, headers):
    response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS', files={'file': file}, headers=headers)
    return response.json() if response.status_code == 200 else None
