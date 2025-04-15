// Admin Dashboard JavaScript

// Handle user approval/rejection
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.approve-user').forEach(button => {
        button.addEventListener('click', function() {
            const username = this.dataset.username;
            approveUser(username, this);
        });
    });

    document.querySelectorAll('.reject-user').forEach(button => {
        button.addEventListener('click', function() {
            const username = this.dataset.username;
            rejectUser(username, this);
        });
    });
});

function approveUser(username, button) {
    fetch(`/admin/approve_user/${username}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const card = button.closest('.approval-card');
            card.style.backgroundColor = '#d4edda';
            setTimeout(() => {
                card.remove();
                checkEmptyState();
            }, 500);
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the request.');
    });
}

function rejectUser(username, button) {
    fetch(`/admin/reject_user/${username}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const card = button.closest('.approval-card');
            card.style.backgroundColor = '#f8d7da';
            setTimeout(() => {
                card.remove();
                checkEmptyState();
            }, 500);
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the request.');
    });
}

function checkEmptyState() {
    const approvalGrid = document.querySelector('.approval-grid');
    if (!approvalGrid.querySelector('.approval-card')) {
        approvalGrid.innerHTML = `
            <div class="no-pending-users">
                <i class="fas fa-check-circle"></i>
                <p>No pending user applications</p>
            </div>`;
    }
}

// Function to update dashboard statistics
function updateDashboardStats() {
    fetch('/admin/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalEmployees').textContent = data.total_employees;
            document.getElementById('presentToday').textContent = data.present_today;
            document.getElementById('pendingLeaves').textContent = data.pending_leaves;
            document.getElementById('absentToday').textContent = data.absent_today;
        });
}

// Function to update pending approvals
function updatePendingApprovals() {
    fetch('/admin/dashboard/pending-approvals')
        .then(response => response.json())
        .then(data => {
            const approvalsList = document.getElementById('pendingApprovalsList');
            approvalsList.innerHTML = ''; // Clear existing content

            if (data.length === 0) {
                approvalsList.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-check-circle"></i>
                        <p>No pending approvals</p>
                    </div>`;
                return;
            }

            data.forEach(item => {
                const approvalItem = document.createElement('div');
                approvalItem.className = 'approval-item';
                approvalItem.innerHTML = `
                    <div class="approval-info">
                        <div class="employee-name">${item.employee_name}</div>
                        <div class="leave-details">
                            <span class="date">${item.start_date} to ${item.end_date}</span>
                            <span class="badge badge-${item.type}">${item.type}</span>
                        </div>
                    </div>
                    <div class="approval-actions">
                        <button class="btn-sm btn-success approve-btn" 
                                data-emp-id="${item.emp_id}" 
                                data-leave-id="${item.leave_id}">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn-sm btn-danger reject-btn"
                                data-emp-id="${item.emp_id}" 
                                data-leave-id="${item.leave_id}">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                approvalsList.appendChild(approvalItem);
            });

            // Reattach event listeners
            attachApprovalEventListeners();
        });
}

// Function to update today's attendance
function updateTodayAttendance() {
    fetch('/admin/dashboard/today-attendance')
        .then(response => response.json())
        .then(data => {
            const attendanceList = document.getElementById('todayAttendanceList');
            attendanceList.innerHTML = ''; // Clear existing content

            if (data.length === 0) {
                attendanceList.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-clock"></i>
                        <p>No attendance records for today</p>
                    </div>`;
                return;
            }

            data.forEach(emp => {
                const attendanceItem = document.createElement('div');
                attendanceItem.className = 'attendance-item';
                attendanceItem.innerHTML = `
                    <div class="employee-info">
                        <div class="avatar">
                            <i class="fas fa-user-circle"></i>
                        </div>
                        <div class="details">
                            <div class="name">${emp.name}</div>
                            <div class="time">
                                <i class="fas fa-clock"></i> ${emp.check_in}
                            </div>
                        </div>
                    </div>
                    <div class="status">
                        <span class="badge badge-success">${emp.status}</span>
                    </div>
                `;
                attendanceList.appendChild(attendanceItem);
            });
        });
}


// Function to attach event listeners to approval buttons
function attachApprovalEventListeners() {
    document.querySelectorAll('.approve-btn, .reject-btn').forEach(button => {
        button.addEventListener('click', function() {
            const empId = this.dataset.empId;
            const leaveId = this.dataset.leaveId;
            const status = this.classList.contains('approve-btn') ? 'approved' : 'rejected';

            fetch('/admin/update_leave', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    employee_id: empId,
                    leave_id: leaveId,
                    status: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the displays
                    updatePendingApprovals();
                    updateDashboardStats();
                }
            });
        });
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    updateDashboardStats();
    updateTodayAttendance();
    updatePendingApprovals();

    // Refresh data every minute
    setInterval(() => {
        updateDashboardStats();
        updateTodayAttendance();
        updatePendingApprovals();
    }, 60000);
});

//Remove Redundant Code Blocks (lines 220-424)