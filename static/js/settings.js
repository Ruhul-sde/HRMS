
// Modal functions
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showAddDepartmentModal() {
    document.getElementById('departmentModalTitle').textContent = 'Add Department';
    document.getElementById('departmentId').value = '';
    document.getElementById('departmentName').value = '';
    showModal('departmentModal');
}

function showAddRoleModal() {
    document.getElementById('roleModalTitle').textContent = 'Add Role';
    document.getElementById('roleId').value = '';
    document.getElementById('roleName').value = '';
    showModal('roleModal');
}

// Department functions
async function saveDepartment(event) {
    event.preventDefault();
    const id = document.getElementById('departmentId').value;
    const name = document.getElementById('departmentName').value;

    try {
        const response = await fetch('/admin/settings/department', {
            method: id ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, name }),
        });

        if (response.ok) {
            location.reload();
        } else {
            alert('Error saving department');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving department');
    }
}

async function editDepartment(id) {
    try {
        const response = await fetch(`/admin/settings/department/${id}`);
        const data = await response.json();
        
        document.getElementById('departmentModalTitle').textContent = 'Edit Department';
        document.getElementById('departmentId').value = id;
        document.getElementById('departmentName').value = data.name;
        showModal('departmentModal');
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading department');
    }
}

async function deleteDepartment(id) {
    if (!confirm('Are you sure you want to delete this department?')) return;

    try {
        const response = await fetch(`/admin/settings/department/${id}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            location.reload();
        } else {
            alert('Error deleting department');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting department');
    }
}

// Role functions
async function saveRole(event) {
    event.preventDefault();
    const id = document.getElementById('roleId').value;
    const name = document.getElementById('roleName').value;

    try {
        const response = await fetch('/admin/settings/role', {
            method: id ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, name }),
        });

        if (response.ok) {
            location.reload();
        } else {
            alert('Error saving role');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving role');
    }
}

async function editRole(id) {
    try {
        const response = await fetch(`/admin/settings/role/${id}`);
        const data = await response.json();
        
        document.getElementById('roleModalTitle').textContent = 'Edit Role';
        document.getElementById('roleId').value = id;
        document.getElementById('roleName').value = data.name;
        showModal('roleModal');
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading role');
    }
}

async function deleteRole(id) {
    if (!confirm('Are you sure you want to delete this role?')) return;

    try {
        const response = await fetch(`/admin/settings/role/${id}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            location.reload();
        } else {
            alert('Error deleting role');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting role');
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}
