<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'

interface ModelPrediction {
  modelName: string;
  willBeLate: boolean;
  prediction: number;
}

interface RangePrediction {
  date?: string;
  quantity?: number;
  prediction: number;
}

interface Props {
  predictions: ModelPrediction[];
  rangePredictions: {
    dates: RangePrediction[];
    quantities: RangePrediction[];
  };
  loading: boolean;
}

const props = defineProps<Props>()
const dateChartRef = ref<HTMLCanvasElement | null>(null)
const qtyChartRef = ref<HTMLCanvasElement | null>(null)
let dateChart: Chart | null = null
let qtyChart: Chart | null = null

const createCharts = () => {
  if (dateChartRef.value && props.rangePredictions?.dates) {
    dateChart?.destroy()
    dateChart = new Chart(dateChartRef.value, {
      type: 'line',
      data: {
        labels: props.rangePredictions.dates.map(d => d.date),
        datasets: [{
          label: 'Predicted Delay (Days)',
          data: props.rangePredictions.dates.map(d => d.prediction),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: props.rangePredictions.dates.map(d => 
            // Highlight current date point
            d.date === props.rangePredictions.dates[10].date ? 8 : 4
          ),
          pointBackgroundColor: props.rangePredictions.dates.map(d => 
            d.date === props.rangePredictions.dates[10].date 
              ? 'rgb(255, 99, 132)' 
              : 'rgb(75, 192, 192)'
          ),
          pointBorderColor: props.rangePredictions.dates.map(d => 
            d.date === props.rangePredictions.dates[10].date 
              ? 'rgb(255, 99, 132)' 
              : 'rgb(75, 192, 192)'
          )
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Predicted Delays (±10 Days)',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Days Late'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date'
            }
          }
        }
      }
    })
  }

  if (qtyChartRef.value && props.rangePredictions?.quantities) {
    qtyChart?.destroy()
    qtyChart = new Chart(qtyChartRef.value, {
      type: 'line',
      data: {
        labels: props.rangePredictions.quantities.map(q => q.quantity?.toFixed(0)),
        datasets: [{
          label: 'Predicted Delay (Days)',
          data: props.rangePredictions.quantities.map(q => q.prediction),
          borderColor: 'rgb(153, 102, 255)',
          backgroundColor: 'rgba(153, 102, 255, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: props.rangePredictions.quantities.map((_, index) => 
            // Highlight current quantity point (middle point)
            index === 10 ? 8 : 4
          ),
          pointBackgroundColor: props.rangePredictions.quantities.map((_, index) => 
            index === 10 
              ? 'rgb(255, 99, 132)' 
              : 'rgb(153, 102, 255)'
          ),
          pointBorderColor: props.rangePredictions.quantities.map((_, index) => 
            index === 10 
              ? 'rgb(255, 99, 132)' 
              : 'rgb(153, 102, 255)'
          )
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Predicted Delays (±100% Quantity)',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Days Late'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Quantity'
            }
          }
        }
      }
    })
  }
}

// Watch for changes in predictions
watch(() => props.rangePredictions, () => {
  createCharts()
}, { deep: true })

onMounted(() => {
  createCharts()
})

onBeforeUnmount(() => {
  // Cleanup charts
  dateChart?.destroy()
  qtyChart?.destroy()
})
</script>

<template>
  <div class="results-container">
    <div v-if="loading" class="spinner-container">
      <div class="spinner"></div>
      <div class="spinner-text">Analyzing delivery time...</div>
    </div>
    <div v-else>
      <div class="predictions-grid">
        <div v-for="pred in predictions" :key="pred.modelName" class="prediction-card">
          <h3>{{ pred.modelName }}</h3>
          <div class="prediction-value">
            <!-- Random Forest only shows will be late -->
            <div v-if="pred.modelName.includes('Random Forest')" 
                 class="prediction-status" 
                 :class="{ 'late': pred.willBeLate }">
              <div class="status-icon">
                <i :class="pred.willBeLate ? 'late-icon' : 'ontime-icon'"></i>
              </div>
              {{ pred.willBeLate ? 'Will be late' : 'On time' }}
            </div>
            <!-- GBR only shows days late -->
            <div v-else>
              <div class="days-late">
                {{ pred.prediction.toFixed(1) }} days late
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="charts-container">
        <div class="chart-card">
          <div class="chart-wrapper">
            <canvas ref="dateChartRef"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-wrapper">
            <canvas ref="qtyChartRef"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results-container {
  margin: 2em auto;
  max-width: 1000px;
  padding: 0 1em;
}

.predictions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5em;
  margin-bottom: 2em;
}

.prediction-card {
  background: white;
  border-radius: 12px;
  padding: 1.5em;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.prediction-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.prediction-card h3 {
  margin: 0 0 1em;
  color: #2c3e50;
  font-size: 1.2em;
}

.prediction-value {
  font-size: 1.8em;
  font-weight: bold;
  text-align: center;
}

.prediction-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;
  color: #28a745;
}

.prediction-status.late {
  color: #dc3545;
}

.status-icon {
  width: 24px;
  height: 24px;
}

.late-icon::before {
  content: "⚠️";
}

.ontime-icon::before {
  content: "✅";
}

.days-late {
  font-size: 0.9em;
  color: #dc3545;
}

.spinner-container {
  text-align: center;
  padding: 3em;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid cadetblue;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

.spinner-text {
  margin-top: 1em;
  color: #666;
  font-size: 1.1em;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2em;
  margin-top: 2em;
}

.chart-card {
  background: white;
  padding: 1.5em;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.chart-wrapper {
  position: relative;
  height: 350px;
  width: 100%;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .predictions-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    height: 300px;
  }
}
</style> 