<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

interface ModelMetrics {
  accuracy?: number;
  cv_score?: number;
  cv_std?: number;
  rmse?: number;
  cv_rmse?: number;
}

interface ModelPrediction {
  modelName: string;
  willBeLate: boolean;
  prediction: number;
  confidence: number;
  metrics: ModelMetrics;
}

const props = defineProps<{
  predictions: Array<ModelPrediction>;
}>()

const chartRef = ref<HTMLCanvasElement | null>(null)
const featureChartRef = ref<HTMLCanvasElement | null>(null)
let predictionChart: Chart | null = null
let featureChart: Chart | null = null

const createPredictionChart = () => {
  if (!chartRef.value || !props.predictions.length) return

  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return

  if (predictionChart) predictionChart.destroy()

  // Filter out classifier (which has prediction = 0)
  const regressionPredictions = props.predictions.filter(p => p.prediction > 0)
  
  const predictions = regressionPredictions.map(p => p.prediction)
  const labels = regressionPredictions.map(p => p.modelName)
  const rmseValues = regressionPredictions.map(p => p.metrics?.cv_rmse || 0)

  predictionChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Predicted Days Late',
        data: predictions,
        backgroundColor: 'rgba(95, 158, 160, 0.6)',
        borderColor: 'cadetblue',
        borderWidth: 1,
        errorBars: {
          plus: rmseValues,
          minus: rmseValues
        }
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Prediction Results with Error Bars'
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const prediction = context.raw
              const rmse = rmseValues[context.dataIndex]
              return [
                `Prediction: ${prediction.toFixed(1)} days`,
                `CV RMSE: ±${rmse.toFixed(2)} days`
              ]
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Days Late'
          }
        }
      }
    }
  })
}

const createFeatureImportanceChart = () => {
  if (!featureChartRef.value || !props.predictions.length) return

  const ctx = featureChartRef.value.getContext('2d')
  if (!ctx) return

  if (featureChart) featureChart.destroy()

  featureChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [
        'Total Quantity',
        'Maragogype Type B',
        'Nairobi Warehouse',
        'Handelskontor Hamburg',
        'Farmers of Brazil'
      ],
      datasets: [{
        label: 'Feature Importance',
        data: [0.228001, 0.077022, 0.067273, 0.057034, 0.056620],
        backgroundColor: 'rgba(95, 158, 160, 0.6)',
        borderColor: 'cadetblue',
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Top 5 Most Important Features'
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              return `Importance: ${(context.raw * 100).toFixed(1)}%`
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Relative Importance (%)'
          }
        }
      }
    }
  })
}

watch(() => props.predictions, () => {
  createPredictionChart()
  createFeatureImportanceChart()
}, { deep: true })

onMounted(() => {
  createPredictionChart()
  createFeatureImportanceChart()
})
</script>

<template>
  <div class="charts-container">
    <div class="chart-wrapper">
      <canvas ref="chartRef"></canvas>
    </div>
    <div class="chart-wrapper">
      <canvas ref="featureChartRef"></canvas>
    </div>
  </div>
</template>

<style scoped>
.charts-container {
  margin: 2em 0;
  display: flex;
  flex-direction: column;
  gap: 2em;
}

.chart-wrapper {
  padding: 1em;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style> 