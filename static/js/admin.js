// Admin Dashboard JavaScript

// Admin functionality for approving/rejecting user registrations
document.addEventListener('DOMContentLoaded', function() {
    // User approval handlers
    const approveButtons = document.querySelectorAll('.approve-user');
    const rejectButtons = document.querySelectorAll('.reject-user');

    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const username = this.dataset.username;
            approveUser(username);
        });
    });

    rejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const username = this.dataset.username;
            rejectUser(username);
        });
    });

    // Leave request handlers
    const leaveApproveButtons = document.querySelectorAll('.approve-btn');
    const leaveRejectButtons = document.querySelectorAll('.reject-btn');

    leaveApproveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const empId = this.dataset.empId;
            const leaveId = this.dataset.leaveId;
            const commentBox = this.closest('.leave-request-card').querySelector('.comment-box');
            const comment = commentBox ? commentBox.value : '';
            updateLeaveStatus(empId, leaveId, 'approved', comment);
        });
    });

    leaveRejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const empId = this.dataset.empId;
            const leaveId = this.dataset.leaveId;
            const commentBox = this.closest('.leave-request-card').querySelector('.comment-box');
            const comment = commentBox ? commentBox.value : '';
            updateLeaveStatus(empId, leaveId, 'rejected', comment);
        });
    });
});

function approveUser(username) {
    fetch(`/admin/approve_user/${username}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('User approved successfully');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while approving the user');
    });
}

function rejectUser(username) {
    fetch(`/admin/reject_user/${username}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('User rejected successfully');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while rejecting the user');
    });
}

function updateLeaveStatus(employeeId, leaveId, status, comment) {
    fetch('/admin/update_leave', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            employee_id: employeeId,
            leave_id: leaveId,
            status: status,
            comment: comment
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Leave request ' + status + ' successfully');
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the leave status');
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