
// Locations JavaScript

// Variables
let map;
let markers = [];

// Initialize map
function initMap() {
    // Default center
    const defaultPosition = { lat: 28.7041, lng: 77.1025 };
    
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: defaultPosition,
        mapTypeId: 'roadmap'
    });
    
    // Try to get user's location to center the map
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                map.setCenter(pos);
            }
        );
    }
    
    // Get all location rows from the table
    const locationRows = document.querySelectorAll('.location-table tbody tr');
    
    locationRows.forEach(row => {
        const name = row.cells[0].textContent;
        const lat = parseFloat(row.cells[1].textContent);
        const lng = parseFloat(row.cells[2].textContent);
        const radius = parseFloat(row.cells[3].textContent);
        
        // Add marker
        addLocationMarker(name, lat, lng, radius);
    });
    
    // Add click event to map for selecting coordinates
    map.addListener('click', function(e) {
        const latInput = document.getElementById('latitude');
        const lngInput = document.getElementById('longitude');
        
        if (latInput && lngInput) {
            latInput.value = e.latLng.lat();
            lngInput.value = e.latLng.lng();
        }
    });
}

// Add location marker with circle radius
function addLocationMarker(name, lat, lng, radius) {
    const marker = new google.maps.Marker({
        position: { lat, lng },
        map: map,
        title: name
    });
    
    // Add circle to represent radius
    const circle = new google.maps.Circle({
        map: map,
        radius: radius,
        fillColor: '#0088ff',
        fillOpacity: 0.2,
        strokeColor: '#0088ff',
        strokeOpacity: 0.5,
        strokeWeight: 1
    });
    
    circle.bindTo('center', marker, 'position');
    
    markers.push({ marker, circle });
    
    // Add info window
    const infoWindow = new google.maps.InfoWindow({
        content: `
            <div>
                <h3>${name}</h3>
                <p>Latitude: ${lat}</p>
                <p>Longitude: ${lng}</p>
                <p>Radius: ${radius}m</p>
            </div>
        `
    });
    
    marker.addListener('click', function() {
        infoWindow.open(map, marker);
    });
}
// Locations management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Location form functionality
    const locationForm = document.querySelector('.location-form');
    
    if (locationForm) {
        locationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('name').value;
            const latitude = parseFloat(document.getElementById('latitude').value);
            const longitude = parseFloat(document.getElementById('longitude').value);
            const radius = parseInt(document.getElementById('radius').value);
            
            if (!name || isNaN(latitude) || isNaN(longitude) || isNaN(radius)) {
                alert('Please fill all fields with valid values.');
                return;
            }
            
            addLocation(name, latitude, longitude, radius);
        });
    }
    
    function addLocation(name, latitude, longitude, radius) {
        fetch('/admin/locations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                latitude: latitude,
                longitude: longitude,
                radius: radius
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Location added successfully.');
                window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the location.');
        });
    }
});

// Google Maps initialization for location management
function initMap() {
    // Check if the map container exists
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    // Default center (can be updated based on user's location)
    const defaultCenter = { lat: 28.7041, lng: 77.1025 };
    
    // Create map
    const map = new google.maps.Map(mapElement, {
        center: defaultCenter,
        zoom: 12,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    });
    
    // Add existing locations to the map
    const locationRows = document.querySelectorAll('.location-table tbody tr');
    const bounds = new google.maps.LatLngBounds();
    const markers = [];
    
    locationRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 3) {
            const name = cells[0].textContent;
            const lat = parseFloat(cells[1].textContent);
            const lng = parseFloat(cells[2].textContent);
            const radius = parseInt(cells[3].textContent);
            
            if (!isNaN(lat) && !isNaN(lng)) {
                const position = { lat, lng };
                
                // Add marker
                const marker = new google.maps.Marker({
                    position: position,
                    map: map,
                    title: name
                });
                markers.push(marker);
                
                // Add info window
                const infoWindow = new google.maps.InfoWindow({
                    content: `<div><strong>${name}</strong><br>Radius: ${radius}m</div>`
                });
                
                marker.addListener('click', function() {
                    infoWindow.open(map, marker);
                });
                
                // Add circle to represent radius
                const circle = new google.maps.Circle({
                    map: map,
                    center: position,
                    radius: radius,
                    fillColor: '#3498db',
                    fillOpacity: 0.2,
                    strokeColor: '#3498db',
                    strokeOpacity: 0.5,
                    strokeWeight: 1
                });
                
                bounds.extend(position);
            }
        }
    });
    
    // Fit map to bounds if we have markers
    if (markers.length > 0) {
        map.fitBounds(bounds);
    }
    
    // Add click listener to allow selecting new location
    map.addListener('click', function(event) {
        const latitude = event.latLng.lat();
        const longitude = event.latLng.lng();
        
        // Update form values
        document.getElementById('latitude').value = latitude.toFixed(6);
        document.getElementById('longitude').value = longitude.toFixed(6);
        
        // Add temporary marker
        markers.forEach(marker => marker.setMap(null));
        markers.length = 0;
        
        const newMarker = new google.maps.Marker({
            position: { lat: latitude, lng: longitude },
            map: map,
            title: 'New Location',
            animation: google.maps.Animation.DROP
        });
        markers.push(newMarker);
    });
}
function validatePassword(password) {
    const minLength = password.length >= 8;
    const hasCapital = /[A-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    const errors = [];
    if (!minLength) errors.push("Password must be at least 8 characters long");
    if (!hasCapital) errors.push("Password must contain at least one capital letter");
    if (!hasNumber) errors.push("Password must contain at least one number");
    if (!hasSpecial) errors.push("Password must contain at least one special character");
    
    return {
        isValid: minLength && hasCapital && hasNumber && hasSpecial,
        errors: errors
    };
}
