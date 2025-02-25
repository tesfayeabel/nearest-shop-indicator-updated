// Preset shop data
const presetShops = [
    {
        name: "Dembel City Center",
        category: "Clothing",
        latitude: 9.005411558649147,
        longitude: 38.767375136234,
        rating: 4.5,
        premium: true,
        distance_km: 1.2
    },
    {
        name: "Friendship City Center",
        category: "Mall",
        latitude: 8.990296814288943,
        longitude: 38.78606833782132,
        rating: 4.8,
        premium: false,
        distance_km: 0.8
    },
    {
        name: "Centery Mall",
        category: "Cinema",
        latitude: 9.01976695073015,
        longitude: 38.81381316439278,
        rating: 4.2,
        premium: false,
        distance_km: 5
    },
    {
        name: "Shoa Supermarket",
        category: "Supermarket",
        latitude: 8.957756153636755,
        longitude: 38.72633646439691,
        rating: 4.6,
        premium: true,
        distance_km: 3.0
    },
    {
        name: "Salem's Ethiopia",
        category: "Coffee",
        latitude: 8.993865726279626,
        longitude: 38.79247819323031,
        rating: 4.6,
        premium: true,
        distance_km: 2.0
    }
];

let map;
let markers = [];
let currentSortBy = 'distance';
let isPremiumOnly = false;

// Initialize map
function initMap() {
    map = L.map('map').setView([9.005411558649147, 38.767375136234], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

// Update radius display
document.getElementById('radiusRange')?.addEventListener('input', (e) => {
    document.getElementById('radiusValue').textContent = e.target.value;
    searchShops();
});

// Search shops function
function searchShops() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const category = document.getElementById('categoryFilter').value;
    const radius = parseFloat(document.getElementById('radiusRange').value);

    let filteredShops = presetShops.filter(shop => {
        const matchesSearch = shop.name.toLowerCase().includes(searchQuery);
        const matchesCategory = category === '' || shop.category === category;
        const withinRadius = shop.distance_km <= radius;
        const meetsPremium = !isPremiumOnly || shop.premium;
        return matchesSearch && matchesCategory && withinRadius && meetsPremium;
    });

    // Sort shops
    filteredShops.sort((a, b) => {
        if (currentSortBy === 'rating') {
            return b.rating - a.rating;
        }
        return a.distance_km - b.distance_km;
    });

    displayResults(filteredShops);
}

// Display results function
function displayResults(shops) {
    const resultsDiv = document.getElementById('shopResults');
    if (!resultsDiv) return;
    
    resultsDiv.innerHTML = '';

    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    shops.forEach(shop => {
        // Create result card
        const card = document.createElement('div');
        card.className = 'border p-4 rounded-lg hover:bg-gray-50 cursor-pointer';
        card.innerHTML = `
            <h3 class="font-semibold">${shop.name}</h3>
            <p class="text-sm text-gray-600">Category: ${shop.category}</p>
            <p class="text-sm text-gray-600">Distance: ${shop.distance_km.toFixed(2)} km</p>
            <p class="text-sm text-gray-600">Rating: ${shop.rating} ⭐</p>
            ${shop.premium ? '<span class="text-xs bg-yellow-200 px-2 py-1 rounded">Premium</span>' : ''}
        `;

        // Add click event to center map on this shop
        card.addEventListener('click', () => {
            map.setView([shop.latitude, shop.longitude], 15);
        });

        resultsDiv.appendChild(card);

        // Add marker to map
        const marker = L.marker([shop.latitude, shop.longitude])
            .bindPopup(`
                <b>${shop.name}</b><br>
                Category: ${shop.category}<br>
                Rating: ${shop.rating} ⭐
            `)
            .addTo(map);
        markers.push(marker);
    });

    // Fit map bounds to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

// Event listeners
document.getElementById('searchInput')?.addEventListener('input', searchShops);
document.getElementById('categoryFilter')?.addEventListener('change', searchShops);
document.getElementById('sortDistance')?.addEventListener('click', () => {
    currentSortBy = 'distance';
    searchShops();
});
document.getElementById('sortRating')?.addEventListener('click', () => {
    currentSortBy = 'rating';
    searchShops();
});
document.getElementById('filterPremium')?.addEventListener('click', () => {
    isPremiumOnly = !isPremiumOnly;
    document.getElementById('filterPremium').classList.toggle('bg-blue-500');
    document.getElementById('filterPremium').classList.toggle('text-white');
    searchShops();
});

// Initialize
window.addEventListener('load', () => {
    if (document.getElementById('map')) {
        initMap();
        searchShops();
    }
});