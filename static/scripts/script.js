const cards = document.querySelector('.cards');
const btnSearch = document.querySelector('.btn-search');
const searchInput = document.querySelector('.search-input');
const maxDistanceText = document.querySelector('.max-distance');
const maxDistanceEl = document.querySelector('#city-distance');
let cityList;
// const DATA_API_ADRESS = 'http://127.0.0.1:8000/therapists'; //for local usage
const DATA_API_ADRESS = 'https://shalomavihail.pythonanywhere.com/therapists'
const DATA_FILE = '../data/data.json';
const CITY_COORDINATE_FILE = '../data/city_coordinates.json';
var HMO_clicked;
async function loadData() {
  // cityList = await getCitiesList();
  maxDistanceText.textContent = maxDistanceEl.value;
  document.addEventListener('DOMContentLoaded', function() {
    // Get the select element by its ID
    const selectElement = document.getElementById('healthcare-provider');
  
    // Add an event listener for the 'change' event
    selectElement.addEventListener('change', function() {
      // Get the value of the selected option
      const selectedValue = this.value;
      
      // Log the selected option's value to the console
      console.log('Selected healthcare provider:', selectedValue);
  
      // Example of doing something based on the selected option
      switch (selectedValue) {
        case 'כללית':
          HMO_clicked = 'כללית';
          // Perform some action here
          break;
        case 'מכבי':
          HMO_clicked = 'מכבי';
          // Perform some action here
          break;
        case 'מאוחדת':
          HMO_clicked = 'מאוחדת';
          // Perform some action here
          break;
        default:
          console.log('Please select a healthcare provider');
      }
    });
  });
  try {
    const fallbackResponse = await fetch(
      `/DATA_FILE`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!fallbackResponse.ok) {
      throw new Error('Fallback fetch failed');
    }
    const data = await fallbackResponse.json();
    data.forEach((card) => {
      // if(card.HMO === HMO_clicked) {
        createTherapistCard(card);
        HMO_clicked = card.HMO;
      // }
    });
  } catch (fallbackError) {
    console.error('Fallback fetch also failed:', fallbackError);
    throw fallbackError;
  }
}

function createTherapistCard(therapistDetails) {
  const {
    name,
    address,
    region,
    profession,
    languages,
    phone,
    gender,
    notes,
    city,
    distance
  } = therapistDetails;
  const card = document.createElement('li');
  card.classList.add('card');

  let genderClass = '';
  if (gender === 'נקבה') {
    genderClass = 'female';
  }

  card.innerHTML = `
      <div class="profile-image ${genderClass}"></div>
      <h2 class="name">${name}</h2>
      <hr class="line-break">
      <p><i class="fa-solid fa-venus-mars"></i>${gender}</p>
      <hr class="line-break"/>
      <p><i class="fa-solid fa-language"></i>${languages}</p>
      <hr class="line-break" />
      <p><i class="fa-solid fa-city"></i>${city}</p>
      <hr class="line-break"/>
      <p><i class="fa-solid fa-location-dot"></i>${address}</p>
      <hr class="line-break"/>
      <p><i class="fa-solid fa-briefcase"></i>${profession}</p>
      <hr class="line-break"/>
      <p><i class="fa-solid fa-phone"></i><a class="phone-link" href='tel:${phone}'>${phone}</a></p>
      <hr class="line-break"/>
      <p><i class="fa-solid"></i>${HMO_clicked}</p>
      <hr class="line-break"/>
      `;


  cards.appendChild(card);
}
async function filterTherapistsByCity(city, maxDistance) {
  try {
    const response = await fetch(
      `${DATA_API_ADRESS}/search_therapists/${city}/${maxDistance}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  } catch (error) {
    displayError(error, city);
    throw new Error('Error filtering therapists:', error);
  }
}

function displayError(error, search_term) {
  const messege = document.querySelector('.message');
  messege.classList.add('show', 'error-message');
  messege.innerHTML = `עיר ${search_term} לא נמצאה, אנא חפשו שוב`;
  setTimeout(() => {
    messege.classList.remove('show', 'error-message');
  }, 5000);
}

// async function getCitiesList() {
//   try {
//     const response = await fetch(CITY_COORDINATE_FILE);
//     if (!response.ok) {
//       throw new Error(`Failed to load city coordinates: ${response.statusText}`);
//     }
//     cityList = await response.json();
//     return cityList;
//   } catch (error) {
//     console.error('Error loading city list:', error);
//     return {}; // Return an empty object to prevent further errors
//   }
// }


function showDropdown(event) {
  let dropdown = document.getElementById('myDropdown');

  let resultList = [];
  const searchTerm = searchInput.value.trim().toLowerCase();

  // Filter cityList based on search term
  const filteredCities = Object.keys(cityList).filter((city) =>
    city.toLowerCase().includes(searchTerm)
  );

  // Display filtered cities as dropdown options
  dropdown.innerHTML = ''; // Clear previous options
  if (filteredCities.length > 0) {
    filteredCities.forEach((city) => {
      const option = document.createElement('div');
      option.textContent = city;
      option.addEventListener('click', () => {
        searchInput.value = city; // Set input value to selected city
        dropdown.classList.remove('show');
      });
      dropdown.appendChild(option);
    });
    dropdown.classList.add('show');
    searchInput.classList.add('hide-bottom');
  } else {
    dropdown.classList.remove('show');
    searchInput.classList.remove('hide-bottom');
  }
}

function displayCities(event) {
  showDropdown(event);
}

window.onclick = function (event) {
  if (!event.target.matches('.dropdown')) {
    let dropdowns = document.getElementsByClassName('dropdown-content');
    for (let i = 0; i < dropdowns.length; i++) {
      let openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
    if (searchInput.classList.contains('hide-bottom')) {
      searchInput.classList.remove('hide-bottom');
    }
  }
};

searchInput.addEventListener('keydown', displayCities);

maxDistanceEl.addEventListener('input', () => {
  maxDistanceText.textContent = maxDistanceEl.value;
});

btnSearch.addEventListener('click', async (e) => {
  e.preventDefault();
  const searchTerm = searchInput.value.trim().toLowerCase();

  if (searchTerm !== '') {
    const message = document.querySelector('.message');
    const maxDistance = maxDistanceEl.value;

    try {
      const result = await filterTherapistsByCity(searchTerm, maxDistance);
      const filteredData = result[0];
      const city_name = result[1];

      cards.innerHTML = ''; // Clear previous cards
      message.classList.add('search-message');
      message.classList.add('show');
      message.innerHTML = `מציג תוצאות עבור ${maxDistance} ק"מ מ${city_name}:`;
      filteredData.forEach(createTherapistCard);
    } catch (error) {
      console.error('Error filtering therapists:', error);
      message.classList.remove('search-message');
      message.classList.remove('show');
      displayError(error, searchTerm);
      loadData();
    }
  }
  searchInput.value = ''; // Clear input after search
});

loadData();
