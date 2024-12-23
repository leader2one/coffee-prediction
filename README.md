# Coffee Delivery Prediction

A machine learning application to predict coffee delivery delays.

## How to run
## Copy settings template
- copy local.settings.template.json to local.settings.json
- Update local.settings.json with your Azure credentials
## Quick Start with Docker

1. Navigate to project root:
```bash
cd coffee-prediction
```

2. Build Docker image:
```bash
docker build -t coffee:latest .
```

3. Run container:
```bash
docker run -d -p 7071:7071 -p 5173:5173 coffee:latest
```

4. Access the application:
   - Wait approximately 5 minutes for all services to start, check docker log if you want
   - Open [http://localhost:5173](http://localhost:5173) in your browser

## Manual Setup

If you prefer running without Docker:

1. Setup Backend:
```bash
cd backend

# Start backend
func start
```

2. Setup Frontend:
```bash
cd frontend
# Install dependencies
yarn install
# Start development server
yarn dev --host
```

The application will be available at [http://localhost:5173](http://localhost:5173)


