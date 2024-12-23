<template>
  <div class="prediction-container">
    <div class="prediction-form">
      <h2>Delivery Time Prediction</h2>
      
      <div class="form-group">
        <label for="supplier">Supplier:</label>
        <select 
          id="supplier" 
          v-model="selectedSupplier"
          :class="{ 'is-invalid': showError && !selectedSupplier }"
        >
          <option value="">Select a supplier</option>
          <option v-for="supplier in suppliers" :key="supplier" :value="supplier">
            {{ supplier }}
          </option>
        </select>
        <div class="error-message" v-if="showError && !selectedSupplier">
          Please select a supplier
        </div>
      </div>

      <div class="form-group">
        <label for="quantity">Quantity:</label>
        <input 
          id="quantity" 
          type="number" 
          v-model="quantity"
          min="0"
          step="1"
          :class="{ 'is-invalid': showError && quantity <= 0 }"
        />
        <div class="error-message" v-if="showError && quantity <= 0">
          Please enter a valid quantity
        </div>
      </div>

      <div class="form-group">
        <label for="orderDate">Order Date:</label>
        <input 
          id="orderDate" 
          type="date" 
          v-model="orderDate"
          :min="minDate"
          :max="maxDate"
          :class="{ 'is-invalid': showError && !orderDate }"
        />
        <div class="error-message" v-if="showError && !orderDate">
          Please select a date
        </div>
      </div>

      <button 
        class="predict-button"
        @click="handlePredict"
        :disabled="loading"
      >
        <span v-if="loading" class="button-spinner"></span>
        {{ loading ? 'Analyzing...' : 'Predict Delivery Time' }}
      </button>
    </div>

    <ModelResults 
      v-if="predictions.length > 0"
      :predictions="predictions"
      :range-predictions="rangePredictions"
      :loading="loading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ModelResults from './ModelResults.vue'

const backendUrl = computed(() => import.meta.env.VITE_APP_BACKEND_URL)
const selectedSupplier = ref('')
const quantity = ref(0)
const orderDate = ref(new Date().toISOString().split('T')[0])
const loading = ref(false)
const predictions = ref([])
const rangePredictions = ref({
  dates: [],
  quantities: []
})
const showError = ref(false)

// Date constraints
const minDate = new Date().toISOString().split('T')[0]
const maxDate = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

const suppliers = [
  'Aromatico',
  'Beans Inc.',
  'Fair Trade AG',
  'Farmers of Brazil',
  'Handelskontor Hamburg'
]

const handlePredict = async () => {
  showError.value = true
  
  if (!selectedSupplier.value || quantity.value <= 0 || !orderDate.value) {
    return
  }

  loading.value = true
  predictions.value = []
  showError.value = false
  
  try {
    const response = await fetch(
      `${backendUrl.value}/score_model?` + 
      `supplier=${encodeURIComponent(selectedSupplier.value)}&` +
      `quantity=${encodeURIComponent(quantity.value)}&` +
      `orderDate=${encodeURIComponent(orderDate.value)}`
    )
    
    if (!response.ok) {
      throw new Error('Failed to get prediction')
    }

    const data = await response.json()
    if (data.predictions) {
      predictions.value = data.predictions
      rangePredictions.value = data.range_predictions
    }
  } catch (error) {
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.prediction-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2em;
}

.prediction-form {
  max-width: 600px;
  margin: 0 auto 3em;
  padding: 2em;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 1.5em;
}

.form-group {
  margin: 1.5em 0;
}

label {
  display: block;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: #2c3e50;
}

select, input {
  width: 100%;
  padding: 0.8em;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.2s;
}

select:focus, input:focus {
  outline: none;
  border-color: cadetblue;
}

.is-invalid {
  border-color: #dc3545;
}

.error-message {
  color: #dc3545;
  font-size: 0.9em;
  margin-top: 0.5em;
}

.predict-button {
  width: 100%;
  padding: 1em;
  background-color: cadetblue;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;
}

.predict-button:hover:not(:disabled) {
  background-color: #4a7a7a;
}

.predict-button:disabled {
  background-color: #a3c1c1;
  cursor: not-allowed;
}

.button-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #ffffff;
  border-top: 3px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .prediction-container {
    padding: 1em;
  }
  
  .prediction-form {
    padding: 1.5em;
  }
}
</style>
