# Imports
import os
import json
import requests
from web3 import Web3
import streamlit as st
from io import BytesIO
from exams import Exams # Custom Exams module
from datetime import datetime
from dotenv import load_dotenv
from metadata import create_metadata, pin_to_ipfs # Custom metadata module
from download import PDF # Custom module to create PDF

# Load environment variables
load_dotenv()

WEB3_RPC = os.getenv('WEB3_RPC')
SMART_CONTRACT_ADDRESS = os.getenv('SMART_CONTRACT_ADDRESS')
PINATA_API_KEY = os.getenv('PINATA_API_KEY')
PINATA_SECRET_API_KEY = os.getenv('PINATA_SECRET_API_KEY')

# Connect to the blockchain
w3 = Web3(Web3.HTTPProvider(WEB3_RPC))

# Load contract ABI
with open('contracts/compiled/contract_abi.json') as f:
    contract_abi = json.load(f)

# Instantiate contract
learning_platform = w3.eth.contract(address=SMART_CONTRACT_ADDRESS, abi=contract_abi)

# Declare accounts as global variable to be accessed by mutiple functions
accounts = w3.eth.accounts

# Pinata headers
headers = {
    'pinata_api_key': PINATA_API_KEY,
    'pinata_secret_api_key': PINATA_SECRET_API_KEY,
}

# Pin to IPFS
def pin_to_ipfs(file):
    # Use the 'file' directly as it is an UploadedFile object
    response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS', files={'file': file}, headers=headers)
    return response.json() if response.status_code == 200 else None

# Main panel
def main_page():
    st.title("Skillified")
    st.write("Your On-Chain Education & Skills Verification Platform")
    image_url = "https://ipfs.io/ipfs/QmX7vXcFZgoTe8pwEqChUT8A641Gu5CfGcHNu6LKWgp45Z?filename=blockchain%26web3_certificate.png" # Replace with your actual image URL
    st.image(image_url, width=350)
    user_address = st.selectbox('Select Your Ethereum Address:', accounts)
    if st.button('Login'): # When the login button is clicked
        st.session_state.logged_in = True # Mark the user as logged in
        st.session_state.user_address = user_address # Store the selected user address
        st.experimental_rerun() # Rerun the app to refresh the page

# Function to authenticate user address
def authenticate():
    # Let the user select their address from a dropdown
    user_address = st.selectbox('Select Your Ethereum Address:', accounts)
    return user_address

# Function to ensure admin cannot create duplicate courses
def is_course_title_duplicate(course_title):
    # Retrieve available courses
    course_count = learning_platform.functions.courseCount().call()
    for i in range(course_count):
        existing_course_title = learning_platform.functions.courses(i).call()[1] # Title is at index 1
        if existing_course_title == course_title:
            return True
    return False

# Admin panel
def admin_panel(user_address):
    st.title('Admin Portal')
    course_title = st.text_input('Course Title')
    instructor_address = st.selectbox('Select The Instructors Address:', accounts)
    course_file = st.file_uploader('Upload Course Material')
    certificate_file = st.file_uploader('Upload Certificate Image')  # Certificate image uploader
    course_fee = st.number_input('Enter Course Fee in ETH:', min_value=0.0)  # Course fee input

    # Dropdown to select an exam for the course
    exam_titles = list(Exams.keys())
    selected_exam_title = st.selectbox('Select Exam for the Course:', exam_titles)

    # Check if the course title matches the selected exam title
    if course_title != selected_exam_title:
        st.error("The course title and exam title must match!")
        return

    # Check for duplicate course title
    if is_course_title_duplicate(course_title):
        st.error("A course with this title already exists!")
        return

    # Check for required inputs
    if not (course_title and instructor_address and course_file and certificate_file and selected_exam_title):
        st.error("All fields are required to create a course!")
        return
    # Create course button
    if st.button('Create Course') and course_file and certificate_file:
        # Initialise a progress bar
        progress_bar = st.progress(0)

        # Update progress to 10% after initiating the process
        progress_bar.progress(10)

        ipfs_hash = pin_to_ipfs(course_file)
        # Update progress to 30% after pinning the course file
        progress_bar.progress(30)

        certificate_ipfs_hash = pin_to_ipfs(certificate_file)  # Pin certificate image to IPFS
        # Update progress to 60% after pinning the certificate image
        progress_bar.progress(60)

        if ipfs_hash and certificate_ipfs_hash:
            # Convert the fee to Wei
            fee_in_wei = w3.toWei(course_fee, 'ether')
            tx_hash = learning_platform.functions.createCourse(course_title, instructor_address, ipfs_hash['IpfsHash'], selected_exam_title, certificate_ipfs_hash['IpfsHash'], fee_in_wei).transact({'from': user_address})
            # Update progress to 100% after course creation is complete
            progress_bar.progress(100)
            st.success(f"Course Created! Transaction Hash: {tx_hash.hex()}")
        else:
            st.warning("Failed to upload to IPFS")
            progress_bar.empty()

# Instructor panel
def instructor_panel(user_address):
    st.title('Instructor Portal')

    # Get the course count from the contract
    course_count = learning_platform.functions.courseCount().call()

    # Check if there are any courses available
    if course_count == 0:
        st.warning("No courses are available at this time. Please check back later.")
        return  # Exit the function since no courses are available

    # Check if the user is an instructor for any course
    is_instructor = False
    for i in range(course_count):
        if user_address == learning_platform.functions.courses(i).call()[2]:  # Instructor address is at index 2
            is_instructor = True
            break

    # Check if the user is the admin
    is_admin = user_address == learning_platform.functions.owner().call()

    # Button to display all courses and the students enrolled
    if st.button('View Enrollments'):
        if is_admin or is_instructor:
            student_addresses = learning_platform.functions.getStudentAddresses().call()
            for student_address in student_addresses:
                enrollments = learning_platform.functions.getEnrollments(student_address).call()
                for enrollment in enrollments:
                    course_id = enrollment[0]
                    student_name = enrollment[2]
                    course_title = learning_platform.functions.courses(course_id).call()[1]  # Title is at index 1
                    enrollment_date = datetime.utcfromtimestamp(enrollment[4]).strftime('%Y-%m-%d')  # Enrollment date is at index 4
                    quiz_result = learning_platform.functions.examResults(course_id, student_address).call()
                    is_passed = quiz_result[2]
                    completion_date_timestamp = learning_platform.functions.getCompletionDate(course_id, student_address).call()
                    completion_date = datetime.utcfromtimestamp(completion_date_timestamp).strftime('%Y-%m-%d')
                    if completion_date == '1970-01-01':
                        completion_date = "Not Completed"

                    status = "Not Attempted"
                    if quiz_result[3] != 0:  # Check if the timestamp is set
                        status = "Passed" if is_passed else "Failed"

                    st.info(f"Course: {course_title} (ID: {course_id}), Student Name: {student_name}, Address: {student_address}, Enrollment Date: {enrollment_date}, Exam Status: {status}, Completion Date: {completion_date}")
        else:
            st.warning("Only the Contract Owner/Instructor can view Enrollments")

    # Let the user select address from a dropdown
    student_address = st.selectbox('Select Student Address:', accounts)

    # Check if the student_address is a valid address
    if not Web3.isAddress(student_address):
        st.error("The provided student address is not valid")

    # Check if the student_address is in the correct checksum format
    elif student_address != Web3.toChecksumAddress(student_address):
        st.error("The provided student address is not in the correct checksum format")
    else:
        # If everything is fine, proceed to call the function
        enrollments = learning_platform.functions.getEnrollments(student_address).call()

    # Retrieve available courses and create a mapping from title to ID
    course_options = []
    for i in range(course_count):
        course = learning_platform.functions.courses(i).call()
        course_title = course[1]
        course_options.append(course_title)

    # Dropdown to select a course by title
    selected_course_title = st.selectbox('Course Name', course_options)

    # Find the corresponding course ID and student name from the student's enrollments
    enrollments = learning_platform.functions.getEnrollments(student_address).call()
    course_id = None
    student_name = None
    for enrollment in enrollments:
        enrolled_course_id = enrollment[0]
        enrolled_course_title = learning_platform.functions.courses(enrolled_course_id).call()[1]
        if enrolled_course_title == selected_course_title:
            course_id = enrolled_course_id
            student_name = enrollment[2]  # Getting the student name from enrollment
            break

    # Check if the student is enrolled in the selected course
    if course_id is None or student_name is None:
        st.error(f"The student is not enrolled in the course {selected_course_title}. You cannot mark completion and issue a certificate.")
    else:
        if st.button('Mark Completion and Issue Certificate') and course_id is not None and student_name is not None:
            # Check if the student is enrolled in the selected course
            if course_id is None or student_name is None:
                st.error(f"The student is not enrolled in the course {selected_course_title}. You cannot mark completion and issue a certificate.")
                return

        # Check the completion date
        completion_date_timestamp = learning_platform.functions.getCompletionDate(course_id, student_address).call()
        completion_date = datetime.utcfromtimestamp(completion_date_timestamp).strftime('%Y-%m-%d')

        # If the completion date is not the Unix epoch, then the course is already completed
        if completion_date != '1970-01-01':
            st.error(f"The student has already completed the course {selected_course_title}. You cannot mark completion and issue a certificate more than once.")
            return

        instructor_address = learning_platform.functions.courses(course_id).call()[2]
        if user_address != instructor_address and user_address != learning_platform.functions.owner().call():
            st.error("You are not authorised to mark completion or issue a certificate for this course.")
            return
        
        # Initialise progress bar
        progress_bar = st.progress(0)
        progress_text = st.empty()

        # # Retrieve the course details using the selected course ID - Incremental progress
        selected_course_details = learning_platform.functions.courses(course_id).call()
        progress_bar.progress(10)

        # Extract course fee in ETH - Incremental progress
        selected_course_fee_in_wei = selected_course_details[7] # Adjust the index according to your contract structure
        selected_course_fee = Web3.fromWei(selected_course_fee_in_wei, 'ether')
        progress_bar.progress(20)

        # Create metadata object
        enrollment_date_timestamp = learning_platform.functions.getEnrollmentDate(course_id, student_address).call()
        enrollment_date_formatted = datetime.utcfromtimestamp(enrollment_date_timestamp).strftime('%Y-%m-%d')
        completion_date_formatted = datetime.now().strftime('%Y-%m-%d')
        instructor_address = learning_platform.functions.courses(course_id).call()[2]
        exam_result = learning_platform.functions.examResults(course_id, student_address).call()
        is_passed = exam_result[2]
        exam_status = "Passed" if is_passed else "Failed"

        # Creating metadata - Incremental progress
        metadata = create_metadata(
            certificate_id=str(course_id),
            course_title=selected_course_title,
            course_fee=str(selected_course_fee),
            instructor_address=instructor_address,
            student_name=student_name,
            student_address=student_address,
            enrollment_date=enrollment_date_formatted,
            exam_status=exam_status,
            completion_date=completion_date_formatted,
        )
        metadata_file = BytesIO(metadata.encode())
        progress_bar.progress(50)

        # Pin metadata to IPFS
        metadata_ipfs_hash = pin_to_ipfs(metadata_file)['IpfsHash']

        # Fetch the token ID for the certificate
        token_count = learning_platform.functions.balanceOf(student_address).call()
        for i in range(token_count):
            token_id = learning_platform.functions.tokenOfOwnerByIndex(student_address, i).call()
            certificate_ipfs_hash, _, _ = learning_platform.functions.getCertificate(token_id).call()
            if token_id == course_id:  # Check if the token ID matches the selected course ID
                break

        # Marking complete & issuing certificate - Incremental progress
        tx_hash = learning_platform.functions.markCompletionAndIssueCertificate(
            course_id, student_address, student_name, metadata_ipfs_hash
        ).transact({'from': user_address})
        progress_bar.progress(100)
        st.success(f"Completion Marked and Certificate Issued! Transaction Hash: {tx_hash.hex()}")

    # Section to view Exam results
    st.subheader('View Student Exam Results')
    course_name_to_view = st.selectbox('Enter Course Name to View Exam Results', course_options)
    student_address_to_view = st.text_input('Enter Student Address to View Exam Results')

    # Find the corresponding course ID for the selected course name
    course_id_to_view = None
    for i in range(course_count):
        course = learning_platform.functions.courses(i).call()
        if course[1] == course_name_to_view:
            course_id_to_view = i
            break

    # Ensure the student address is in the correct format
    if student_address_to_view:
        student_address_to_view = Web3.toChecksumAddress(student_address_to_view)

    # Retrieve the instructor's address for the selected course ID
    instructor_address = learning_platform.functions.courses(course_id_to_view).call()[2]  # Instructor address is at index 2

    if user_address == instructor_address or user_address == learning_platform.functions.owner().call():
        if student_address_to_view and course_id_to_view is not None:  # Check if the student address is provided
            # Check if the student is enrolled in the course
            enrollments = learning_platform.functions.getEnrollments(student_address_to_view).call()
            is_enrolled = any(enrollment[0] == course_id_to_view for enrollment in enrollments)

            if is_enrolled:
                exam_result = learning_platform.functions.examResults(course_id_to_view, student_address_to_view).call()
                is_passed = exam_result[2]  # Accessing the isPassed by index 2
                st.info(f"Course ID: {course_id_to_view}, Passed: {'✅' if is_passed else '❌'}")
            else:
                st.error(f"The student is not enrolled in the course {course_name_to_view}.")
        else:
            st.warning("Please enter a valid student address.")
    else:
        st.error("You are not authorised to view this information.")

# Student panel
def student_panel(user_address):
    # Accessing the session state
    session_state = st.session_state

    # Initialise session state if not already initialised
    if 'taking_exam' not in session_state:
        session_state.taking_exam = {}
        session_state.enrolled_courses = []  # Tracking enrolled courses

    st.title('Student Portal')

    # Retrieve available courses
    course_count = learning_platform.functions.courseCount().call()

    # Check if there are any courses available
    if course_count == 0:
        st.warning("No courses are available at this time. Please check back later.")
        return  # Exit the function since no courses are available
    
    course_options = []
    for i in range(course_count):
        course = learning_platform.functions.courses(i).call()
        course_options.append((course[0], course[1], course[3], Web3.fromWei(course[7], 'ether')))  # Storing course ID, title, IPFS hash, and fee in ether

    # Dropdown to select a course, including the fee in the display
    selected_course = st.selectbox('Select a Course', course_options, format_func=lambda x: f"{x[1]} (Fee: {x[3]} ETH)")
    selected_course_id, selected_course_title, selected_ipfs_hash, selected_course_fee = selected_course

    # Add a new state variable to track if the download button was clicked
    if 'download_clicked' not in session_state:
        session_state.download_clicked = False

    # Student name input
    student_name = st.text_input('Enter Your Name to Enroll or Download Your Certificate')

    # Check if the "Enroll" button is clicked and the student name is not empty
    if st.button('Enroll'):
        if student_name:  # Check if the student name is not empty
            # Check if the student is already enrolled in the selected course
            if selected_course_id not in session_state.enrolled_courses:
                selected_course_fee_in_wei = Web3.toWei(selected_course_fee, 'ether')  # Convert the fee to wei
                
                # Check if the student's balance is greater than or equal to the course fee
                student_balance = w3.eth.getBalance(user_address)
                if student_balance >= selected_course_fee_in_wei:
                    tx_hash = learning_platform.functions.enrollInCourse(selected_course_id, student_name).transact({'from': user_address, 'value': selected_course_fee_in_wei})
                    st.success(f"Enrolled in {selected_course_title} Successfully! Transaction Hash: {tx_hash.hex()}")
                    session_state.enrolled_courses.append(selected_course_id)  # Add to enrolled courses
                else:
                    st.error("You have insufficient funds to enroll in this course.")
            else:
                st.warning("You are already enrolled in this course.")  # Display a warning if already enrolled
        else:
            st.error("Please enter your name before enrolling.")  # Display an error message if the name is not entered

    # Check if download was clicked without entering a name
    if session_state.download_clicked and not student_name:
        st.warning("Please Enter Your Name to Download Your Certificate")

    # Check if the student is enrolled in the selected course
    if selected_course_id in session_state.enrolled_courses:
        # Check if the student has already passed the exam
        quiz_result = learning_platform.functions.examResults(selected_course_id, user_address).call()
        is_passed = quiz_result[2]

        if not is_passed:
            # Begin Course button
            begin_course_key = f'begin_course_{selected_course_id}'
            if st.button(f'Begin Course: {selected_course_title}', key=begin_course_key):
                course_url = f"https://ipfs.io/ipfs/{selected_ipfs_hash}"
                st.markdown(f"[Click here to open the course material]({course_url})")
                # Embed autoplaying study music audio using HTML
                audio_file_url = "https://ipfs.io/ipfs/QmazrLqVKC1MAwyMjnrvL5YuRL8h4U5H1ZRhc4SpSyP85w?filename=interloodle.mp3"
                st.markdown(f'<audio src="{audio_file_url}" autoplay loop></audio>', unsafe_allow_html=True)
                
            # Take Exam button
            take_exam_key = f'take_exam_{selected_course_id}'
            if st.button(f'Take Exam: {selected_course_title}', key=take_exam_key):
                session_state.taking_exam[selected_course_id] = True  # Set the state for the specific course

        if session_state.taking_exam.get(selected_course_id):
            quiz_function = Exams[selected_course_title]
            is_passed = quiz_function(user_address, selected_course_id, course_count)
            exam_status = "Passed" if is_passed else "Failed"

            if is_passed:
                # Disable the "Take Exam" button by removing its state
                session_state.taking_exam[selected_course_id] = False  # Reset the state for the specific course

                # Create metadata object
                enrollment_date_timestamp = learning_platform.functions.getEnrollmentDate(selected_course_id, user_address).call()
                enrollment_date_formatted = datetime.utcfromtimestamp(enrollment_date_timestamp).strftime('%Y-%m-%d')
                completion_date_formatted = datetime.now().strftime('%Y-%m-%d')
                instructor_address = learning_platform.functions.courses(selected_course_id).call()[2]
        
                metadata = create_metadata(
                    certificate_id=str(selected_course_id),
                    course_title=selected_course_title,
                    course_fee=str(selected_course_fee),
                    instructor_address=instructor_address,
                    student_name=student_name,
                    student_address=user_address,
                    enrollment_date=enrollment_date_formatted,
                    exam_status=exam_status,
                    completion_date=completion_date_formatted,
                )
                metadata_file = BytesIO(metadata.encode())

                # Pin metadata to IPFS
                metadata_ipfs_hash = pin_to_ipfs(metadata_file)['IpfsHash']

                tx_hash = learning_platform.functions.markCompletionAndIssueCertificate(
                    selected_course_id, user_address, student_name, metadata_ipfs_hash
                ).transact({'from': user_address})
                # Embed autoplaying audio using HTML
                audio_file_url = "https://ipfs.io/ipfs/QmazrLqVKC1MAwyMjnrvL5YuRL8h4U5H1ZRhc4SpSyP85w?filename=interloodle.mp3"
                st.markdown(f'<audio src="{audio_file_url}" autoplay loop></audio>', unsafe_allow_html=True)
                st.success(f"Completion Marked and Certificate Issued! Transaction Hash: {tx_hash.hex()}")
            else:
                st.warning("You have not passed the exam.")

    # View owned certificates
    st.subheader('My Certificates')
    token_count = learning_platform.functions.balanceOf(user_address).call()

    # Create a list to hold the certificate information
    certificates = []
    for i in range(token_count):
        token_id = learning_platform.functions.tokenOfOwnerByIndex(user_address, i).call()
        certificate_ipfs_hash, _, completion_date = learning_platform.functions.getCertificate(token_id).call()
        # Convert the completion_date (timestamp) to a human-readable date format
        completion_date_formatted = datetime.utcfromtimestamp(completion_date).strftime('%Y-%m-%d')
    
        # Fetch the course details
        course_id = token_id 
        course_details = learning_platform.functions.courses(course_id).call()
        course_title = course_details[1] 

        certificates.append((course_title, certificate_ipfs_hash, completion_date_formatted))

    # Loop through the certificates and display them in rows of 3
    for i in range(0, len(certificates), 3):
        cols = st.columns(3)  # Create 3 columns for the row
        for j in range(3):
            idx = i + j
            if idx < len(certificates):
                course_title, certificate_ipfs_hash, completion_date_formatted = certificates[idx]
                certificate_url = f"https://ipfs.io/ipfs/{certificate_ipfs_hash}"
                with cols[j]:  # Place each certificate in one of the columns
                    st.image(certificate_url, caption=course_title, width=150)
                    st.write(f"Completed: {completion_date_formatted}")
                
                    if student_name:  # Check if the student name is not empty
                        pdf_buffer = PDF(certificate_ipfs_hash, student_name, selected_course_title, completion_date_formatted)
                    
                        # Create a download link
                        st.download_button(
                            label="Download Certificate",
                            data=pdf_buffer,
                            file_name=f"{course_title}_certificate.pdf",
                            mime="application/pdf",
                        )
                    else:
                    # Create a dummy download button that updates the state variable
                        if st.button("Download Certificate", key=f"download_{idx}"):
                            session_state.download_clicked = True

# Main login page
def main():
    # Initialise session state for logged_in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # If the user is not logged in, display the main page
    if not st.session_state.logged_in:
        main_page()
        return

    # If the user is logged in, proceed to the admin panel
    user_address = st.session_state.user_address # Retrieve the user address from session state
    st.sidebar.title("Skillified")
    st.sidebar.header("Your On-Chain Education & Skills Verification Platform")
    image_url = "https://ipfs.io/ipfs/QmX7vXcFZgoTe8pwEqChUT8A641Gu5CfGcHNu6LKWgp45Z?filename=blockchain%26web3_certificate.png" # Replace with your actual image URL
    # Display the image in the sidebar
    st.sidebar.image(image_url, width=250)
    st.sidebar.header('Navigation')
    user_role = st.sidebar.selectbox('Select Role', ['Admin', 'Instructor', 'Student'])

    # Add a logout button to the sidebar
    if st.sidebar.button('Logout'):
        # Clear the session state related to the logged-in user
        st.session_state.enrolled_courses = []
        st.session_state.taking_exam = {}
        st.session_state.logged_in = False # Set the logged_in state to False
        st.experimental_rerun() # Rerun the app to refresh the page
        
    if user_role == 'Admin':
        admin_panel(user_address)
    
    elif user_role == 'Instructor':
        instructor_panel(user_address)

    elif user_role == 'Student':
        student_panel(user_address)
# Check whether the current script is being run as the main program
if __name__ == "__main__":
    main()






















