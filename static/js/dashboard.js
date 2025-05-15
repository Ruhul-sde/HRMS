let userPosition = null;

function handleLocationError(error) {
    let message;
    switch(error.code) {
        case error.PERMISSION_DENIED:
            message = "Please allow location access in your browser to mark attendance. Click the location icon in your address bar and allow access.";
            break;
        case error.POSITION_UNAVAILABLE:
            message = "Unable to detect your location. Please ensure your device's GPS/Location service is enabled.";
            break;
        case error.TIMEOUT:
            message = "Location request timed out. Please check your internet connection and try again.";
            break;
        default:
            message = "Unable to get location. Please ensure location services are enabled on your device and browser.";
            break;
    }
    document.getElementById('locationStatus').innerHTML = 
        `<div class="alert alert-danger">${message} <button onclick="getLocation()" class="btn btn-sm btn-primary ml-2">Try Again</button></div>`;
}

async function getLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            handleLocationError({ code: 0, message: "Geolocation not supported by your browser" });
            resolve(false);
            return;
        }

        const options = {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        };

        // Clear any previous location status
        document.getElementById('locationStatus').innerHTML = 
            '<div class="alert alert-info">Requesting location access...</div>';

        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (position && position.coords) {
                    userPosition = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    document.getElementById('locationStatus').innerHTML = 
                        '<div class="alert alert-success">Location acquired successfully!</div>';
                    resolve(true);
                } else {
                    handleLocationError({ code: 2, message: "Unable to get location coordinates" });
                    resolve(false);
                }
            },
            (error) => {
                // Show more specific error for permission denied
                if (error.code === 1) {
                    document.getElementById('locationStatus').innerHTML = 
                        `<div class="alert alert-danger">
                            Please allow location access in your browser. 
                            <br>Click the location/GPS icon in your browser's address bar and select "Allow".
                            <br><button onclick="getLocation()" class="btn btn-sm btn-primary mt-2">Try Again</button>
                        </div>`;
                } else {
                    handleLocationError(error);
                }
                resolve(false);
            },
            options
        );
    });
}

async function getLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            handleLocationError({ code: 0, message: "Geolocation not supported" });
            resolve(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                document.getElementById('locationStatus').innerHTML = 
                    '<div class="alert alert-success">Location acquired successfully!</div>';
                resolve(true);
            },
            (error) => {
                handleLocationError(error);
                resolve(false);
            }
        );
    });
}

async function markAttendance(isCheckout) {
    try {
        const confirmLocationBtn = document.getElementById('confirmLocation');
        const locationStatus = document.getElementById('locationStatus');

        confirmLocationBtn.disabled = true;
        confirmLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        if (!userPosition) {
            const locationAcquired = await getLocation();
            if (!locationAcquired) {
                confirmLocationBtn.disabled = false;
                confirmLocationBtn.innerHTML = isCheckout ? 'Confirm Check-out' : 'Confirm Check-in';
                return;
            }
        }

        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: userPosition.lat,
                longitude: userPosition.lng,
                is_checkout: isCheckout
            })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('attendanceMessage').innerHTML = 
                `<div class="alert alert-success">${data.message}</div>`;

            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            locationStatus.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            confirmLocationBtn.disabled = false;
            confirmLocationBtn.innerHTML = isCheckout ? 'Confirm Check-out' : 'Confirm Check-in';
        }
    } catch (error) {
        console.error('Attendance marking error:', error);
        document.getElementById('locationStatus').innerHTML = 
            '<div class="alert alert-danger">Error marking attendance. Please try again.</div>';
        document.getElementById('confirmLocation').disabled = false;
        document.getElementById('confirmLocation').innerHTML = isCheckout ? 'Confirm Check-out' : 'Confirm Check-in';
    }
}

document.getElementById('markAttendanceBtn')?.addEventListener('click', function() {
    document.getElementById('locationModal').style.display = 'block';
    const confirmLocationBtn = document.getElementById('confirmLocation');
    confirmLocationBtn.setAttribute('data-mode', 'checkin');
    confirmLocationBtn.innerHTML = 'Confirm Check-in';
    getLocation();
});

let map, userMarker;

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,
        styles: [
            {
                "featureType": "all",
                "elementType": "geometry",
                "stylers": [{"color": "#f5f5f5"}]
            },
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{"color": "#e9e9e9"}]
            }
        ]
    });

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                if (userMarker) userMarker.setMap(null);
                userMarker = new google.maps.Marker({
                    position: pos,
                    map: map,
                    title: 'Your Location',
                    animation: google.maps.Animation.DROP
                });

                map.setCenter(pos);
                document.getElementById('locationCoordinates').textContent = 
                    `${pos.lat.toFixed(6)}, ${pos.lng.toFixed(6)}`;
            },
            () => {
                handleLocationError(true);
            }
        );
    }
}

document.getElementById('checkoutBtn')?.addEventListener('click', function() {
    document.getElementById('locationModal').style.display = 'block';
    const confirmLocationBtn = document.getElementById('confirmLocation');
    confirmLocationBtn.setAttribute('data-mode', 'checkout');
    confirmLocationBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Confirm Check-out';
    initMap();
});

document.querySelector('.close')?.addEventListener('click', function() {
    document.getElementById('locationModal').style.display = 'none';
});

document.getElementById('confirmLocation')?.addEventListener('click', function() {
    const isCheckout = this.getAttribute('data-mode') === 'checkout';
    markAttendance(isCheckout);
});

function calculateWorkingTime(checkIn, checkOut) {
    if (!checkIn || !checkOut) return "N/A";

    const convertTime12to24 = (time12h) => {
        const [time, modifier] = time12h.split(' ');
        let [hours, minutes] = time.split(':');

        if (hours === '12') {
            hours = '00';
        }

        if (modifier === 'PM') {
            hours = parseInt(hours, 10) + 12;
        }

        return `${hours}:${minutes}`;
    };

    const time1 = convertTime12to24(checkIn);
    const time2 = convertTime12to24(checkOut);

    const [hours1, minutes1] = time1.split(':');
    const [hours2, minutes2] = time2.split(':');

    const date1 = new Date(2000, 0, 1, hours1, minutes1);
    const date2 = new Date(2000, 0, 1, hours2, minutes2);

    const diff = date2 - date1;
    const hours = Math.floor(diff / 1000 / 60 / 60);
    const minutes = Math.floor((diff / 1000 / 60) % 60);

    return `${hours}h ${minutes}m`;
}