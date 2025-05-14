// Main JavaScript file for BookMyDocAI

// DOM Elements
const loginArea = document.getElementById('login-area');
const userArea = document.getElementById('user-area');
const userIdSpan = document.getElementById('user-id');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const idInput = document.getElementById('id-input');
const welcomeArea = document.getElementById('welcome-area');
const chatArea = document.getElementById('chat-area');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const doctorList = document.getElementById('doctor-list');
const specializationList = document.getElementById('specialization-list');
const exampleModal = document.getElementById('example-modal');
const closeModal = document.querySelector('.close');
const queryItems = document.querySelectorAll('.query-item');
const loadingIndicator = document.getElementById('loading-indicator');

// State
let isLoggedIn = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in (from session storage)
    const userId = sessionStorage.getItem('userId');
    if (userId) {
        loginUser(userId);
    }
    
    // Load doctors and specializations
    fetchDoctorsAndSpecializations();
    
    // Add event listeners
    setupEventListeners();
});

// Set up event listeners for interactive elements
function setupEventListeners() {
    // Login button
    loginBtn.addEventListener('click', () => {
        const idValue = idInput.value.trim();
        if (validateId(idValue)) {
            loginWithId(idValue);
        } else {
            showNotification('Please enter a valid 7-8 digit ID number', 'error');
        }
    });
    
    // ID input - allow enter key to submit
    idInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const idValue = idInput.value.trim();
            if (validateId(idValue)) {
                loginWithId(idValue);
            } else {
                showNotification('Please enter a valid 7-8 digit ID number', 'error');
            }
        }
    });
    
    // Logout button
    logoutBtn.addEventListener('click', logoutUser);
    
    // Message send button
    sendBtn.addEventListener('click', sendMessage);
    
    // Message input - allow enter key to submit
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Close modal
    closeModal.addEventListener('click', () => {
        exampleModal.classList.remove('show');
    });
    
    // Close modal when clicking outside the content
    window.addEventListener('click', (e) => {
        if (e.target === exampleModal) {
            exampleModal.classList.remove('show');
        }
    });
    
    // Query items in modal
    queryItems.forEach(item => {
        item.addEventListener('click', () => {
            const query = item.getAttribute('data-query');
            messageInput.value = query;
            exampleModal.classList.remove('show');
            
            // If logged in, focus the input
            if (isLoggedIn) {
                messageInput.focus();
            }
        });
    });
    
    // Add a help button to the chat area
    const helpButton = document.createElement('button');
    helpButton.innerHTML = '<i class="fas fa-question-circle"></i> Example Queries';
    helpButton.classList.add('help-button');
    helpButton.style.position = 'absolute';
    helpButton.style.top = '10px';
    helpButton.style.right = '10px';
    
    helpButton.addEventListener('click', () => {
        exampleModal.classList.add('show');
    });
    
    chatArea.style.position = 'relative';
    chatArea.appendChild(helpButton);
}

// Validate ID format (7-8 digits)
function validateId(id) {
    return /^\d{7,8}$/.test(id);
}

// Login with ID
function loginWithId(id) {
    showLoading();
    
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_number: id }),
    })
    .then(response => {
        hideLoading();
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Login failed');
            });
        }
        return response.json();
    })
    .then(data => {
        loginUser(id);
        showNotification('Login successful', 'success');
    })
    .catch(error => {
        showNotification(error.message, 'error');
    });
}

// Login user (update UI)
function loginUser(id) {
    isLoggedIn = true;
    sessionStorage.setItem('userId', id);
    
    // Update UI
    loginArea.classList.add('hidden');
    userArea.classList.remove('hidden');
    userIdSpan.textContent = `ID: ${id}`;
    
    // Show chat area, hide welcome
    welcomeArea.classList.add('hidden');
    chatArea.classList.remove('hidden');
    
    // Focus message input
    messageInput.focus();
    
    // Add welcome message if not already present
    if (chatMessages.childElementCount <= 1) {
        addBotMessage("Hello! I'm your AI assistant for BookMyDocAI. How can I help you today? You can book, cancel, or reschedule appointments, or check doctor availability.");
    }
}

// Logout user
function logoutUser() {
    showLoading();
    
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        hideLoading();
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Logout failed');
            });
        }
        return response.json();
    })
    .then(data => {
        // Clear state
        isLoggedIn = false;
        sessionStorage.removeItem('userId');
        
        // Update UI
        loginArea.classList.remove('hidden');
        userArea.classList.add('hidden');
        idInput.value = '';
        
        // Show welcome, hide chat
        welcomeArea.classList.remove('hidden');
        chatArea.classList.add('hidden');
        
        // Clear chat messages except the initial one
        while (chatMessages.childElementCount > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
        
        showNotification('Logged out successfully', 'success');
    })
    .catch(error => {
        showNotification(error.message, 'error');
    });
}

// Send message to the server
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to the chat
    addUserMessage(message);
    
    // Clear input
    messageInput.value = '';
    
    // Send to server
    showLoading();
    
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    })
    .then(response => {
        hideLoading();
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to send message');
            });
        }
        return response.json();
    })
    .then(data => {
        // Add bot response to the chat
        addBotMessage(data.message);
    })
    .catch(error => {
        addBotMessage('Sorry, I encountered an error processing your request. Please try again.');
        showNotification(error.message, 'error');
    });
}

// Add user message to the chat
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    messageElement.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// Add bot message to the chat
function addBotMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot';
    messageElement.innerHTML = `
        <div class="message-content">
            <p>${formatMessage(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// Format message (convert line breaks to HTML)
function formatMessage(message) {
    return escapeHtml(message).replace(/\n/g, '<br>');
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fetch doctors and specializations from the server
function fetchDoctorsAndSpecializations() {
    fetch('/doctors')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch doctors and specializations');
            }
            return response.json();
        })
        .then(data => {
            // Populate doctors list
            data.doctors.forEach(doctor => {
                const doctorElement = document.createElement('div');
                doctorElement.className = 'doctor-item';
                doctorElement.innerHTML = `
                    <i class="fas fa-user-md"></i>
                    <span>Dr. ${capitalizeWords(doctor)}</span>
                `;
                doctorElement.addEventListener('click', () => {
                    if (isLoggedIn) {
                        messageInput.value = `Is Dr. ${capitalizeWords(doctor)} available tomorrow?`;
                        messageInput.focus();
                    } else {
                        // Show login prompt
                        showNotification('Please login first to check doctor availability', 'info');
                    }
                });
                doctorList.appendChild(doctorElement);
            });
            
            // Populate specializations list
            data.specializations.forEach(spec => {
                const specElement = document.createElement('div');
                specElement.className = 'specialization-item';
                specElement.innerHTML = `
                    <i class="fas fa-stethoscope"></i>
                    <span>${formatSpecialization(spec)}</span>
                `;
                specElement.addEventListener('click', () => {
                    if (isLoggedIn) {
                        messageInput.value = `Show me available ${formatSpecialization(spec).toLowerCase()}s for tomorrow`;
                        messageInput.focus();
                    } else {
                        // Show login prompt
                        showNotification('Please login first to check specialization availability', 'info');
                    }
                });
                specializationList.appendChild(specElement);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Format specialization (replace underscores with spaces and capitalize)
function formatSpecialization(spec) {
    return capitalizeWords(spec.replace(/_/g, ' '));
}

// Capitalize words in a string
function capitalizeWords(str) {
    return str
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Show loading indicator
function showLoading() {
    loadingIndicator.classList.remove('hidden');
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

// Show notification
function showNotification(message, type) {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        document.body.removeChild(existingNotification);
    }
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}