# Imports
import os
import json
import streamlit as st
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WEB3_RPC = os.getenv('WEB3_RPC')
SMART_CONTRACT_ADDRESS = os.getenv('SMART_CONTRACT_ADDRESS')

# Load contract ABI
with open('contracts/compiled/contract_abi.json') as f:
    contract_abi = json.load(f)

# Connect to the blockchain
w3 = Web3(Web3.HTTPProvider(WEB3_RPC))

# Instantiate contract
learning_platform = w3.eth.contract(address=SMART_CONTRACT_ADDRESS, abi=contract_abi)

# Introduction to Python Exam
def introduction_to_python_exam(user_address, course_id, course_count):
    st.title('Introduction to Python Exam')
    questions = [
        {'question': 'What is the correct way to comment a line in Python?', 'options': ['// this is a comment', '/* this is a comment */', '# this is a comment'], 'answer': 2},
        {'question': 'What data type is the result of: 5 + 3.14?', 'options': ['int', 'float', 'str'], 'answer': 1},
        {'question': 'How do you create a function in Python?', 'options': ['def function_name():', 'function function_name()', 'function function_name:{}'], 'answer': 0},
        {'question': 'Which of the following is not a valid variable name?', 'options': ['my_var', 'my-var', 'myVar'], 'answer': 1},
        {'question': 'How do you create a list in Python?', 'options': ['list = {}', 'list = []', 'list = ()'], 'answer': 1},
        {'question': 'What will the output be: print(10 % 3)?', 'options': ['3', '1', '0'], 'answer': 1},
        {'question': 'Which method would you use to add an item to the end of a list?', 'options': ['push()', 'add()', 'append()'], 'answer': 2},
        {'question': 'How do you start a loop that continues until `i` is 5?', 'options': ['while i < 5:', 'while (i < 5)', 'while i = 5:'], 'answer': 0},
        {'question': 'How do you import a library in Python?', 'options': ['import library_name', 'using library_name', '#include library_name'], 'answer': 0},
        {'question': 'Which function is used to read user input?', 'options': ['input()', 'read()', 'scan()'], 'answer': 0}
    ]
    # Collect answers
    answers = []
    for q in questions:
        st.write(q['question'])
        answer = st.radio('Choose an answer', q['options'])
        answers.append(q['options'].index(answer))

    # Check answers
    is_passed = all(answers[i] == questions[i]['answer'] for i in range(len(questions)))

    # Record result on blockchain
    if st.button('Submit Exam'):
        tx_hash = learning_platform.functions.recordExamResult(course_id, is_passed).transact({'from': user_address})
        result_message = "Congratulations, you passed!" if is_passed else "Sorry, you did not pass."
        st.write(result_message)
        st.success(f"Result Recorded! Transaction Hash: {tx_hash.hex()}")
    
        if is_passed:  # Only show balloons if the student has passed
            st.balloons() 
    
        return is_passed

    return False


# Machine Learning exam
def machine_learning_exam(user_address, course_id, course_count):
    st.title('Machine Learning Exam')
    questions = [
        {'question': 'Which of the following is a supervised learning method?', 'options': ['K-Means', 'Linear Regression', 'PCA'], 'answer': 1},
        {'question': 'What is the commonly used loss function for classification problems?', 'options': ['Mean Squared Error', 'Cross-Entropy', 'Both of the above'], 'answer': 1},
        {'question': 'Which of the following is not a type of machine learning?', 'options': ['Supervised Learning', 'Unsupervised Learning', 'Uncontrolled Learning'], 'answer': 2},
        {'question': 'What does SVM stand for in machine learning?', 'options': ['Simple Vector Machine', 'Support Vector Machine', 'Sequential Vector Machine'], 'answer': 1},
        {'question': 'Which algorithm is used to partition an unlabeled dataset?', 'options': ['K-Means Clustering', 'Linear Regression', 'Logistic Regression'], 'answer': 0},
        {'question': 'In machine learning, what does overfitting refer to?', 'options': ['Model performs poorly on unseen data', 'Model performs well on unseen data', 'Model performs equally on all data'], 'answer': 0},
        {'question': 'What is the goal of regression in machine learning?', 'options': ['Classify data into categories', 'Predict a continuous value', 'Group data into clusters'], 'answer': 1},
        {'question': 'Which of the following is a popular neural network framework?', 'options': ['TensorFlow', 'Pandas', 'Scikit-learn'], 'answer': 0},
        {'question': 'What is the process of dividing data into training and testing sets called?', 'options': ['Data Splitting', 'Data Cleaning', 'Data Extraction'], 'answer': 0},
        {'question': 'Which of the following algorithms relies on Bayes theorem?', 'options': ['Naive Bayes', 'Random Forest', 'Gradient Boosting'], 'answer': 0}
    ]
    # Collect answers
    answers = []
    for q in questions:
        st.write(q['question'])
        answer = st.radio('Choose an answer', q['options'])
        answers.append(q['options'].index(answer))

    # Check answers
    is_passed = all(answers[i] == questions[i]['answer'] for i in range(len(questions)))

    # Record result on blockchain
    if st.button('Submit Exam'):
        tx_hash = learning_platform.functions.recordExamResult(course_id, is_passed).transact({'from': user_address})
        result_message = "Congratulations, you passed!" if is_passed else "Sorry, you did not pass."
        st.write(result_message)
        st.success(f"Result Recorded! Transaction Hash: {tx_hash.hex()}")
    
        if is_passed:  # Only show balloons if the student has passed
            st.balloons() 
    
        return is_passed

    return False

    
# Blockchain & Web3 Exam
def blockchain_and_web3_exam(user_address, course_id, course_count):
    st.title('Blockchain and Web3 Exam')
    questions = [
        {'question': 'What does the term "Blockchain" refer to?', 'options': ['A type of database', 'A programming language', 'A web framework'], 'answer': 0},
        {'question': 'What is the primary cryptocurrency used on the Ethereum network?', 'options': ['Bitcoin', 'Ether', 'Litecoin'], 'answer': 1},
        {'question': 'What is the standard for creating smart contracts on Ethereum?', 'options': ['ERC-20', 'Solidity', 'ERC-721'], 'answer': 1},
        {'question': 'Which of the following is a decentralized app (dApp)?', 'options': ['Facebook', 'Google Maps', 'CryptoKitties'], 'answer': 2},
        {'question': 'Which consensus algorithm is commonly used in public blockchains?', 'options': ['Proof of Work', 'Proof of Identity', 'Proof of Stake'], 'answer': 0},
        {'question': 'What is a smart contract?', 'options': ['A legal document', 'A self-executing contract with code', 'A type of cryptocurrency'], 'answer': 1},
        {'question': 'What is the main advantage of decentralized systems?', 'options': ['Speed', 'Censorship resistance', 'Ease of use'], 'answer': 1},
        {'question': 'What does Web3 enable users to do?', 'options': ['Create websites', 'Interact with decentralised networks', 'Speed up internet connection'], 'answer': 1},
        {'question': 'What is a hard fork in blockchain?', 'options': ['A security feature', 'A type of wallet', 'A major update that is not backward compatible'], 'answer': 2},
        {'question': 'Which programming language is commonly used to write Ethereum smart contracts?', 'options': ['Python', 'Java', 'Solidity'], 'answer': 2}
    ]
    # Collect answers
    answers = []
    for q in questions:
        st.write(q['question'])
        answer = st.radio('Choose an answer', q['options'])
        answers.append(q['options'].index(answer))

    # Check answers
    is_passed = all(answers[i] == questions[i]['answer'] for i in range(len(questions)))

    # Record result on blockchain
    if st.button('Submit Exam'):
        tx_hash = learning_platform.functions.recordExamResult(course_id, is_passed).transact({'from': user_address})
        result_message = "Congratulations, you passed!" if is_passed else "Sorry, you did not pass."
        st.write(result_message)
        st.success(f"Result Recorded! Transaction Hash: {tx_hash.hex()}")
    
        if is_passed:  # Only show balloons if the student has passed
            st.balloons() 
    
        return is_passed

    return False

# Contain Exams within a dictionary named exams which can be imported to main skillified.py script
Exams = {
    "Introduction to Python": introduction_to_python_exam,
    "Machine Learning": machine_learning_exam,
    "Blockchain & Web3": blockchain_and_web3_exam
}