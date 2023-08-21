// SPDX-License-Identifier: UNLICENSED
// Specify the version of Solidity
pragma solidity ^0.8.1;

// Import ERC721Enumerable contract from OpenZeppelin library
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

// Declare the contract, inheriting from ERC721Enumerable for NFT functionality
contract LearningPlatform is ERC721Enumerable {
    // Declare the owner variable
    address public owner;

    // Define a Course struct with relevant properties
    struct Course {
        uint256 id;
        string title;
        address instructor;
        string ipfsHash; // IPFS hash for course content
        string examTitle;
        string certificateIpfsHash; // IPFS hash for certificate
        bool isActive;
        uint256 fee;
    }

    // Define an Enrollment struct for tracking student enrollments
    struct Enrollment {
        uint256 courseId;
        address student;
        string studentName;
        bool isCompleted;
        uint256 enrollmentDate;
    }

    // Define a Certificate struct for tracking issued certificates
    struct Certificate {
        string certificateIpfsHash; // IPFS hash for the certificate
        string metadataIpfsHash; // IPFS hash for the metadata
        uint256 completionDate;
    }

    // Define a QuizResult struct to track student exam results
    struct ExamResult {
        uint256 courseId;
        address student;
        bool isPassed;
        uint256 passedTimestamp; // Timestamp when the student passed
    }

    // Define mappings to store various data structures
    mapping(uint256 => Course) public courses;
    mapping(address => Enrollment[]) public enrollments;
    mapping(uint256 => Certificate) public certificates;
    mapping(uint256 => mapping(address => ExamResult)) public examResults; // Nested mapping by courseId and student address
    mapping(uint256 => mapping(address => uint256)) public completionDates;

    // Array and mapping to track student addresses and enrollments
    address[] public studentAddresses;
    mapping(address => bool) private hasEnrollment;

    // Variables to keep track of course and certificate counts
    uint256 public courseCount = 0;
    uint256 public certificateCount = 0;

    // Constructor to initialize the contract, setting the owner and name/symbol for the ERC721 token
    constructor() ERC721("Certificate", "CERT") {
        owner = msg.sender;
    }

    // Function to create a new course, only callable by the owner
    function createCourse(string memory _title, address _instructor, string memory _ipfsHash, string memory _examTitle, string memory _certificateIpfsHash, uint256 _fee) public {
        require(msg.sender == owner, "Only the owner can create courses");
        courses[courseCount] = Course(courseCount, _title, _instructor, _ipfsHash, _examTitle, _certificateIpfsHash, true, _fee);
        courseCount++;
    }

    // Function to enroll in a course, verifies course availability and fee before enrolling
    function enrollInCourse(uint256 _courseId, string memory _studentName) public payable {
        require(courses[_courseId].isActive, "Course not available");
        require(msg.value == courses[_courseId].fee, "Incorrect course fee");
        // Transfer the course fee to the instructor
        address instructor = courses[_courseId].instructor;
        payable(instructor).transfer(courses[_courseId].fee);
        // Check and add to the list of students if not already there
        if (!hasEnrollment[msg.sender]) {
            studentAddresses.push(msg.sender);
            hasEnrollment[msg.sender] = true;
        }
        // Create and store the new enrollment
        Enrollment memory newEnrollment = Enrollment({
            courseId: _courseId,
            student: msg.sender,
            studentName: _studentName,
            isCompleted: false,
            enrollmentDate: block.timestamp
        });
        enrollments[msg.sender].push(newEnrollment);
    }

        // Function to retrieve enrollments for a specific student
    function getEnrollments(address _student) public view returns (Enrollment[] memory) {
        return enrollments[_student];
    }

    // Function to retrieve all student addresses
    function getStudentAddresses() public view returns (address[] memory) {
        return studentAddresses;
    }

    // Function to retrieve the enrollment date for a specific course and student
    function getEnrollmentDate(uint256 _courseId, address _student) public view returns (uint256) {
        Enrollment[] storage studentEnrollments = enrollments[_student];
        for (uint i = 0; i < studentEnrollments.length; i++) {
            if (studentEnrollments[i].courseId == _courseId) {
                return studentEnrollments[i].enrollmentDate;
            }
        }
        revert("Enrollment not found");
    }

    // Function to mark a course as completed and issue a certificate
    function markCompletionAndIssueCertificate(uint256 _courseId, address _student, string memory _metadataIpfsHash) public {
        require(courses[_courseId].isActive, "Course not available");
        // Authorization check: Only the instructor, owner or student can issue certificates
        require(msg.sender == _student || courses[_courseId].instructor == msg.sender || msg.sender == owner, "Not authorized");

        Enrollment[] storage studentEnrollments = enrollments[_student];
        bool found = false;
        // Loop through enrollments to find the relevant one
        for (uint i = 0; i < studentEnrollments.length; i++) {
            if (studentEnrollments[i].courseId == _courseId && studentEnrollments[i].student == _student) {
                studentEnrollments[i].isCompleted = true;
                found = true;
                break;
            }
        }

        require(found, "Enrollment not found");

        // Record the completion date
        completionDates[_courseId][_student] = block.timestamp;

        // Get the certificate IPFS hash from the course
        string memory certificateIpfsHash = courses[_courseId].certificateIpfsHash;

        // Issue Certificate with both the certificate & metadata IPFS hashes
        certificates[certificateCount] = Certificate(certificateIpfsHash, _metadataIpfsHash, block.timestamp);
        _mint(_student, certificateCount); // Mint the certificate as an NFT
        certificateCount++;
    }

    // Function to issue a certificate for a passed exam
    function issueCertificateForPassedExam(uint256 _courseId, address _student, string memory _metadataIpfsHash) public {
        // Check that the student passed the exam
        ExamResult memory examResult = examResults[_courseId][_student];
        require(examResult.isPassed, "Student did not pass the exam");

        // Check that the student is enrolled in the course
        Enrollment[] storage studentEnrollments = enrollments[_student];
        bool found = false;
        for (uint i = 0; i < studentEnrollments.length; i++) {
            if (studentEnrollments[i].courseId == _courseId && studentEnrollments[i].student == _student) {
                studentEnrollments[i].isCompleted = true;
                found = true;
                break;
            }
        }

        require(found, "Enrollment not found");

        // Record the completion date
        completionDates[_courseId][_student] = block.timestamp;

        // Get the certificate IPFS hash from the course
        string memory certificateIpfsHash = courses[_courseId].certificateIpfsHash;

        // Issue Certificate with both the certificate & metadata IPFS hashes
        certificates[certificateCount] = Certificate(certificateIpfsHash, _metadataIpfsHash, block.timestamp);
        _mint(_student, certificateCount); // Mint the certificate as an NFT
        certificateCount++;
    }

    // Function to record exam results for a specific course
    function recordExamResult(uint256 _courseId, bool _isPassed) public {
        // Ensure the student is enrolled in the course
        Enrollment[] storage studentEnrollments = enrollments[msg.sender];
        bool enrolled = false;
        for (uint i = 0; i < studentEnrollments.length; i++) {
            if (studentEnrollments[i].courseId == _courseId) {
                enrolled = true;
                break;
            }
        }

        require(enrolled, "Not enrolled in the course");
    
        uint256 passedTimestamp = _isPassed ? block.timestamp : 0; // Set the timestamp if the student passed

        // Record the exam result
        examResults[_courseId][msg.sender] = ExamResult(_courseId, msg.sender, _isPassed, passedTimestamp);
    }

    // Function to retrieve the completion date for a specific course and student
    function getCompletionDate(uint256 _courseId, address _student) public view returns (uint256) {
        return completionDates[_courseId][_student];
    }

    // Function to retrieve a specific certificate
    function getCertificate(uint256 _certificateId) public view returns (string memory certificateIpfsHash, string memory metadataIpfsHash, uint256 completionDate) {
        Certificate memory certificate = certificates[_certificateId];
        return (certificate.certificateIpfsHash, certificate.metadataIpfsHash, certificate.completionDate);
    }

    // Override the tokenURI function to return the IPFS hash for the certificate metadata
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_exists(tokenId), "Token does not exist");
        return certificates[tokenId].metadataIpfsHash;
    }

} // End of contract
