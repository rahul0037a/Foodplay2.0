document.addEventListener("DOMContentLoaded", () => {
  // -------------------------------------------
  //  Utility: Notification System
  // -------------------------------------------
  function showNotification(message, type = "error") {
    const notification = document.getElementById("notification");
    notification.innerHTML = `
      <div class="max-w-md mx-auto p-4 rounded shadow-lg text-white ${
        type === "error" ? "bg-red-500" : type === "success" ? "bg-green-500" : "bg-blue-500"
      } animate__animated animate__fadeInDown">
        ${message}
      </div>
    `;
    setTimeout(() => {
      notification.firstElementChild.classList.add("animate__fadeOutUp");
      setTimeout(() => (notification.innerHTML = ""), 500);
    }, 3000);
  }



  // -------------------------------------------
  // 1. Sport and Role Dropdown Setup
  // -------------------------------------------
  const sportRoleMapping = {
    "Cricket": ["Batsman", "Bowler (Fast)", "Bowler (Spin)", "Wicketkeeper", "Fielder"],
    "Football": ["Goalkeeper", "Defender", "Midfielder", "Forward/Striker"],
    "Badminton": ["Singles", "Doubles"],
    "Tennis": ["Singles", "Doubles"],
    "Athletics": ["Sprinter", "Middle-Distance", "Long-Distance", "Field Events"],
    "Casual Gym": ["General"],
    "Sedentary": ["General"]
  };

  const sportRoleMultipliers = {
    "Cricket - Batsman": 1.88,
    "Cricket - Bowler (Fast)": 2.1,
    "Cricket - Bowler (Spin)": 1.9,
    "Cricket - Wicketkeeper": 2.1,
    "Cricket - Fielder": 1.75,
    "Football - Goalkeeper": 1.7,
    "Football - Defender": 2.1,
    "Football - Midfielder": 2.45,
    "Football - Forward/Striker": 2.35,
    "Badminton - Singles": 2.45,
    "Badminton - Doubles": 2.15,
    "Tennis - Singles": 2.35,
    "Tennis - Doubles": 2.15,
    "Athletics - Sprinter": 2.6,
    "Athletics - Middle-Distance": 2.45,
    "Athletics - Long-Distance": 2.7,
    "Athletics - Field Events": 2.15,
    "Casual Gym - General": 1.4,
    "Sedentary - General": 1.2
  };

  const sportSelect = document.getElementById("sport");
  const roleSelect = document.getElementById("role");

  Object.keys(sportRoleMapping).forEach(sport => {
    const option = document.createElement("option");
    option.value = sport;
    option.textContent = sport;
    sportSelect.appendChild(option);
  });

  sportSelect.addEventListener("change", () => {
    roleSelect.innerHTML = "";
    const selectedSport = sportSelect.value;
    const roles = sportRoleMapping[selectedSport] || [];
    roles.forEach(role => {
      const option = document.createElement("option");
      option.value = role;
      option.textContent = role;
      roleSelect.appendChild(option);
    });
    if (roles.length > 0) {
      roleSelect.value = roles[0];
    }
  });
  sportSelect.dispatchEvent(new Event("change"));




  // -------------------------------------------
  // DYNAMIC TRAINING SESSIONS
  // -------------------------------------------
  const sessionCountSelect = document.getElementById("session_count");
  const sessionTimesContainer = document.getElementById("session-times-container");

  // Rebuild the time inputs based on session_count
  function updateSessionTimeInputs() {
    sessionTimesContainer.innerHTML = ""; // clear existing
    const sessionCount = parseInt(sessionCountSelect.value) || 0;
    for (let i = 1; i <= sessionCount; i++) {
      const wrapper = document.createElement("div");
      wrapper.className = "flex flex-col";

      const label = document.createElement("label");
      label.className = "block text-sm font-medium text-gray-700 mb-1";
      label.textContent = `Session ${i} Time`;

      const timeInput = document.createElement("input");
      timeInput.type = "time";
      timeInput.name = `session_time_${i}`;
      timeInput.id = `session_time_${i}`;
      timeInput.required = true; // required if we have a session
      timeInput.className = "mt-1 block w-full rounded-md border-gray-300 shadow-sm";

      wrapper.appendChild(label);
      wrapper.appendChild(timeInput);
      sessionTimesContainer.appendChild(wrapper);
    }
  }

  // Listen for changes to session_count
  sessionCountSelect.addEventListener("change", updateSessionTimeInputs);

  // Initialize once on page load
  updateSessionTimeInputs();

  // -------------------------------------------
  // 3. Display Calculation Results and Macros
  // -------------------------------------------
  function displayResults(result) {
    if (result.error) {
      showNotification(result.error, "error");
      return;
    }
    document.getElementById("bmr-result").textContent = `${result.bmr} kcal`;
    document.getElementById("tdee-result").textContent = `${result.tdee} kcal`;
    document.getElementById("calorie-result").textContent = `${result.daily_caloric_intake} kcal`;

    const nutrientsContainer = document.getElementById("nutrients-info");
    nutrientsContainer.innerHTML = "";
    const nutrients = [
      { label: "Protein", value: result.protein, unit: "g" },
      { label: "Carbohydrates", value: result.carbohydrates, unit: "g" },
      { label: "Fats", value: result.fats, unit: "g" },
      { label: "Fibre", value: result.fibre, unit: "g" },
      { label: "Saturated Fats", value: result.saturated_fats, unit: "g" }
    ];
    nutrients.forEach(nutrient => {
      const card = document.createElement("div");
      card.className = "bg-gray-100 p-4 rounded-md text-center transition-all duration-300 hover:shadow-xl";
      card.innerHTML = `
        <h3 class="font-semibold text-gray-700">${nutrient.label}</h3>
        <p class="text-2xl font-bold text-green-600">${nutrient.value} ${nutrient.unit}</p>
      `;
      nutrientsContainer.appendChild(card);
    });
    document.getElementById("results").classList.remove("hidden");
  }

  // -------------------------------------------
  // 4. Handle Calculation Form Submission
  // -------------------------------------------
  document.getElementById("personal-info-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    for (let key in data) {
      if (!data[key]) {
        showNotification(`Please fill out the ${key} field.`, "error");
        return;
      }
    }
    data.is_athlete = data.is_athlete.toLowerCase();
    data.diet = data.diet.toLowerCase();
    const selectedSport = data.sport;
    const selectedRole = data.role;
    const sportRoleKey = `${selectedSport} - ${selectedRole}`;
    data.activity = sportRoleMultipliers[sportRoleKey] || 1.2;
    data.sport = selectedSport;
    data.role = selectedRole;
    // Gather session times in an array
    const sessionCount = parseInt(data.session_count) || 0;
    const sessionTimes = [];
    for (let i = 1; i <= sessionCount; i++) {
      const timeKey = `session_time_${i}`;
      if (data[timeKey]) {
        sessionTimes.push(data[timeKey]);
      }
    }
    data.session_times = sessionTimes;

    fetch("/calculate", {  // ✅ Ensure correct Flask URL
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
  })
      .then(response => response.json())
      .then(result => {
        if(result.error) {
          showNotification(result.error, "error");
        } else {
          showNotification("Calculation successful!", "success");
          displayResults(result);
        }
      })
      .catch(error => {
        console.error("Error:", error);
        showNotification("An error occurred while processing your request.", "error");
      });
  });

  // -------------------------------------------
  // 5. Meal Planner with dynamic Meal Count
  // -------------------------------------------
  const suggestMealsBtn = document.getElementById("suggest-meals-btn");
  suggestMealsBtn.addEventListener("click", suggestMealPlan);

  function suggestMealPlan() {
    const calorieResultElem = document.getElementById("calorie-result");
    if (!calorieResultElem || !calorieResultElem.textContent) {
      showNotification("Please calculate your daily caloric intake first.", "error");
      return;
    }
    let dailyCalories = parseFloat(calorieResultElem.textContent.replace(/[^\d.]/g, ''));
    if (isNaN(dailyCalories)) {
      showNotification("Invalid daily caloric intake value.", "error");
      return;
    }
    const mealCount = parseInt(document.getElementById("meal_count").value) || 4;

    // Show spinner while fetching
    suggestMealsBtn.disabled = true;
    document.getElementById("suggest-btn-text").textContent = "Loading...";
    document.getElementById("suggest-spinner").classList.remove("hidden");

    // Grab macros from the displayed results
    const proteinVal = parseFloat(document.querySelector("#nutrients-info div:nth-child(1) p").textContent.replace(/[^\d.]/g, ''));
    const carbVal = parseFloat(document.querySelector("#nutrients-info div:nth-child(2) p").textContent.replace(/[^\d.]/g, ''));
    const fatVal = parseFloat(document.querySelector("#nutrients-info div:nth-child(3) p").textContent.replace(/[^\d.]/g, ''));

    // ADDED: pass diet to /suggest_meals
    const dietPreference = document.getElementById("diet").value;  // <--- get user's diet
    // ...
    fetch("/suggest_meals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        daily_caloric_intake: dailyCalories,
        protein: proteinVal,
        carbohydrates: carbVal,
        fats: fatVal,
        meal_count: mealCount,
        diet: dietPreference             // <--- include diet in the request
      })
    })
    
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          showNotification(data.error, "error");
        } else {
          showNotification("Meal plan generated!", "success");
          displayMealPlan(data);
        }
        suggestMealsBtn.disabled = false;
        document.getElementById("suggest-btn-text").textContent = "Suggest Meal Plan";
        document.getElementById("suggest-spinner").classList.add("hidden");
      })
      .catch(error => {
        console.error("Error fetching meal plan:", error);
        showNotification("An error occurred while fetching the meal plan.", "error");
        suggestMealsBtn.disabled = false;
        document.getElementById("suggest-btn-text").textContent = "Suggest Meal Plan";
        document.getElementById("suggest-spinner").classList.add("hidden");
      });
  }

  function displayMealPlan(plan) {
    const mealPlanSection = document.getElementById("meal-plan");
    const mealPlanContent = document.getElementById("meal-plan-content");
    const mealPlanSummary = document.getElementById("meal-plan-summary");
    mealPlanContent.innerHTML = "";

    // Use the meal categories returned
    const categories = Object.keys(plan.meal_options);
    let selectedPlan = {};

    categories.forEach(cat => {
      const options = plan.meal_options[cat];
      if (options && options.length) {
        const container = document.createElement("div");
        container.className = "mb-4 p-4 border rounded-lg bg-gradient-to-r from-green-100 to-blue-100 shadow-lg transition-transform duration-300 hover:scale-105";
        container.innerHTML = `<h3 class="font-semibold text-lg mb-2">${cat}</h3>`;
        
        options.forEach((option, idx) => {
          const optionId = `${cat}-${idx}`;
          const radioDiv = document.createElement("div");
          radioDiv.className = "flex items-center mb-1";
          radioDiv.innerHTML = `
            <input type="radio" name="${cat}" id="${optionId}" class="mr-2" value="${idx}">
            <label for="${optionId}" class="cursor-pointer">
              <span class="font-medium">${option.food_name}</span> 
              (<span>${option.serving_type}</span>) - 
              <span>${option.calories} kcal, Protein: ${option.protein} g, Carbs: ${option.carbs} g, Fats: ${option.fats} g</span>
            </label>
          `;
          container.appendChild(radioDiv);
        });
        mealPlanContent.appendChild(container);
        const recommendedIdx = options.findIndex(opt => plan.recommended_meal_plan[cat] && opt.food_name === plan.recommended_meal_plan[cat].food_name);
        const defaultIdx = recommendedIdx >= 0 ? recommendedIdx : 0;
        const radios = container.querySelectorAll(`input[name="${cat}"]`);
        radios[defaultIdx].checked = true;
        selectedPlan[cat] = options[defaultIdx];

        radios.forEach(radio => {
          radio.addEventListener("change", () => {
            const idx = parseInt(radio.value);
            selectedPlan[cat] = options[idx];
            updateMealSummary(selectedPlan);
          });
        });
      }
    });
    
    updateMealSummary(selectedPlan);
    mealPlanSection.classList.remove("hidden");
  }

  function updateMealSummary(selectedPlan) {
    const mealPlanSummary = document.getElementById("meal-plan-summary");
    mealPlanSummary.innerHTML = "";
    let totalCalories = 0;
    for (let meal in selectedPlan) {
      const option = selectedPlan[meal];
      totalCalories += option.cal;
      const div = document.createElement("div");
      div.className = "mb-2 p-2 bg-white rounded shadow";
      div.innerHTML = `<strong>${meal}:</strong> ${option.food_name} (${option.cal} kcal)`;
      mealPlanSummary.appendChild(div);
    }
    const totalDiv = document.createElement("div");
    totalDiv.className = "font-semibold text-lg mt-4 p-3 bg-green-200 rounded";
    totalDiv.innerHTML = `Total Calories: ${totalCalories} kcal`;
    mealPlanSummary.appendChild(totalDiv);
  }
});
