
// Leave Balance Management
function saveLeaveBalances(event) {
    event.preventDefault();
    const data = {
        pl: parseInt(document.getElementById('plBalance').value),
        cl: parseInt(document.getElementById('clBalance').value),
        ml: parseInt(document.getElementById('mlBalance').value)
    };

    fetch('/api/admin/settings/leave-balance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Leave balance settings updated successfully');
        } else {
            alert('Error updating leave balance settings');
        }
    });
}

// Department Management
function showAddDepartmentModal() {
    document.getElementById('departmentModalTitle').textContent = 'Add Department';
    document.getElementById('departmentForm').reset();
    document.getElementById('departmentId').value = '';
    document.getElementById('departmentModal').style.display = 'block';
}

function editDepartment(deptName) {
    document.getElementById('departmentModalTitle').textContent = 'Edit Department';
    document.getElementById('departmentName').value = deptName;
    document.getElementById('departmentId').value = deptName;
    document.getElementById('departmentModal').style.display = 'block';
}

function saveDepartment(event) {
    event.preventDefault();
    const data = {
        id: document.getElementById('departmentId').value,
        name: document.getElementById('departmentName').value
    };

    fetch('/api/admin/settings/department', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error saving department');
        }
    });
}

function deleteDepartment(deptName) {
    if (confirm('Are you sure you want to delete this department?')) {
        fetch(`/api/admin/settings/department/${deptName}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error deleting department');
            }
        });
    }
}

// Job Role Management
function showAddRoleModal() {
    document.getElementById('roleModalTitle').textContent = 'Add Role';
    document.getElementById('roleForm').reset();
    document.getElementById('roleId').value = '';
    document.getElementById('roleModal').style.display = 'block';
}

function editRole(roleName) {
    document.getElementById('roleModalTitle').textContent = 'Edit Role';
    document.getElementById('roleName').value = roleName;
    document.getElementById('roleId').value = roleName;
    document.getElementById('roleModal').style.display = 'block';
}

function saveRole(event) {
    event.preventDefault();
    const data = {
        id: document.getElementById('roleId').value,
        name: document.getElementById('roleName').value
    };

    fetch('/api/admin/settings/job-role', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error saving job role');
        }
    });
}

function deleteRole(roleName) {
    if (confirm('Are you sure you want to delete this job role?')) {
        fetch(`/api/admin/settings/job-role/${roleName}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error deleting job role');
            }
        });
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}
