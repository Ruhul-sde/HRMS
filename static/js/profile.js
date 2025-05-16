
function openEditModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeEditModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openPasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function updateProfile(event) {
    event.preventDefault();
    const form = document.getElementById('editProfileForm');
    if (!form) return;

    const formData = new FormData(form);

    fetch('/api/update_profile', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || 'Failed to update profile');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating profile');
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const editModal = document.getElementById('editProfileModal');
    const passwordModal = document.getElementById('changePasswordModal');
    
    if (event.target === editModal) {
        closeEditModal();
    }
    if (event.target === passwordModal) {
        closePasswordModal();
    }
}
