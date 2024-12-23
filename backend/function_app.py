import azure.functions as func
import datetime
import json
import logging
import pickle
import pandas as pd
import numpy as np

app = func.FunctionApp()

def load_models():
    try:
        # Load both models with correct filenames
        rf_model = pickle.load(open('./rf_classifier_model_20241220_140936.pkl', 'rb'))
        gbr_model = pickle.load(open('./gb_regressor_20241220_142030.pkl', 'rb'))
        return rf_model, gbr_model
    except Exception as e:
        logging.error(f"Error loading models: {str(e)}")
        raise

def create_feature_matrix(supplier, quantity, order_date, model_type="gbr"):
    try:
        # Load both models
        rf_model, gbr_model = load_models()
        
        # Get feature names based on model type
        if model_type == "rf":
            feature_names = rf_model.feature_names_in_
            logging.info(f"RF Model features: {feature_names}")
        else:
            feature_names = gbr_model.feature_names_in_
            logging.info(f"GBR Model features: {feature_names}")
        
        # Create base dataframe with all features
        data = pd.DataFrame(0, index=[0], columns=feature_names)
        
        # Set quantity based on model type
        if 'total_qty' in feature_names:
            data['total_qty'] = quantity
        
        # Set supplier based on model type
        supplier_col = f'd_supplier_{supplier}'
        if supplier_col in feature_names:
            data[supplier_col] = 1
        elif f'd_{supplier}' in feature_names:  # Different prefix in RF model
            data[f'd_{supplier}'] = 1
        
        # Parse date
        order_datetime = datetime.datetime.strptime(order_date, '%Y-%m-%d')
        
        # Set date features based on model type
        month_col = f'month_{order_datetime.month}'
        if month_col in feature_names:
            data[month_col] = 1
        
        day_col = f'day_{order_datetime.day}'
        if day_col in feature_names:
            data[day_col] = 1
        
        weekday_col = f'weekday_{order_datetime.weekday()}'
        if weekday_col in feature_names:
            data[weekday_col] = 1
        
        # Log what we're sending
        non_zero = data.loc[0, data.loc[0] != 0]
        logging.info(f"Non-zero features for GBR: {non_zero.to_dict()}")
        
        return data
        
    except Exception as e:
        logging.error(f"Error in create_feature_matrix: {str(e)}")
        raise

def get_model_metrics():
    """Return model metrics from training"""
    return {
        "rf_classifier": {
            "accuracy": 0.9677,
            "cv_score": 0.9693,
            "cv_std": 0.0015
        },
        "gbr": {
            "cv_rmse": 1.8659,
            "cv_std": 0.0342,
            "rmse": 1.8149,
            "r2": 0.8234
        }
    }

def calculate_confidence(prediction, quantity, model_type="gbr"):
    """Calculate confidence based on model type and prediction"""
    metrics = get_model_metrics()
    
    if model_type == "rf":
        base_confidence = metrics["rf_classifier"]["cv_score"]
        qty_factor = min(1.0, 10000 / max(abs(quantity), 1))
        return float(min(max(base_confidence * qty_factor, 0.1), 0.95))
    else:
        # GBR confidence calculation
        gbr_metrics = metrics["gbr"]
        
        # Base confidence from model performance
        base_confidence = 1 / (1 + gbr_metrics["cv_rmse"])
        
        # Quantity factor - reduce confidence for extreme quantities
        # Assuming typical order quantities are between 100 and 10000
        qty_normal = min(max(quantity, 100), 10000) / 10000
        qty_factor = 1 - abs(0.5 - qty_normal)  # Max confidence at qty=5000
        
        # Prediction factor - reduce confidence for larger predictions
        # Assuming most delays are between 0-5 days
        pred_factor = 1 / (1 + abs(prediction) / 5)
        
        # Combine factors with weights
        confidence = (
            0.4 * base_confidence + 
            0.3 * qty_factor + 
            0.3 * pred_factor
        )
        
        # Ensure confidence is between 0.1 and 0.95
        return float(min(max(confidence, 0.1), 0.95))

def get_range_predictions(model, data, base_quantity, base_date, feature_type="date"):
    predictions = []
    
    if feature_type == "date":
        # Get predictions for ±10 days
        base_datetime = datetime.datetime.strptime(base_date, '%Y-%m-%d')
        for i in range(-10, 11):
            new_date = base_datetime + datetime.timedelta(days=i)
            new_data = data.copy()
            
            # Update date features
            month_col = f'month_{new_date.month}'
            day_col = f'day_{new_date.day}'
            weekday_col = f'weekday_{new_date.weekday()}'
            
            for col in new_data.columns:
                if col.startswith(('month_', 'day_', 'weekday_')):
                    new_data[col] = 0
            
            if month_col in new_data.columns:
                new_data[month_col] = 1
            if day_col in new_data.columns:
                new_data[day_col] = 1
            if weekday_col in new_data.columns:
                new_data[weekday_col] = 1
                
            pred = float(model.predict(new_data)[0])
            predictions.append({
                "date": new_date.strftime('%Y-%m-%d'),
                "prediction": max(0, pred)
            })
    else:
        # Get predictions for ±10% quantity
        qty_step = base_quantity * 0.1
        for i in range(-10, 11):
            new_qty = base_quantity + (i * qty_step)
            if new_qty <= 0:
                continue
                
            new_data = data.copy()
            new_data['total_qty'] = new_qty
            
            pred = float(model.predict(new_data)[0])
            predictions.append({
                "quantity": new_qty,
                "prediction": max(0, pred)
            })
    
    return predictions

@app.route(route="score_model", auth_level=func.AuthLevel.ANONYMOUS)
def score_model(req: func.HttpRequest) -> func.HttpResponse:
    try:
        supplier = req.params.get('supplier')
        quantity = float(req.params.get('quantity'))
        order_date = req.params.get('orderDate')
        
        # Load both models
        rf_model, gbr_model = load_models()
        
        # Create features for each model
        rf_data = create_feature_matrix(supplier, quantity, order_date, model_type="rf")
        gbr_data = create_feature_matrix(supplier, quantity, order_date, model_type="gbr")
        
        # Get main predictions
        rf_prediction = bool(rf_model.predict(rf_data)[0])
        gbr_prediction = float(gbr_model.predict(gbr_data)[0])
        
        # Get range predictions
        date_predictions = get_range_predictions(gbr_model, gbr_data, quantity, order_date, "date")
        quantity_predictions = get_range_predictions(gbr_model, gbr_data, quantity, order_date, "quantity")
        
        # Create response
        response_data = {
            "predictions": [
                {
                    "modelName": "Random Forest Classifier",
                    "willBeLate": rf_prediction,
                    "prediction": 0
                },
                {
                    "modelName": "Gradient Boosting Regressor",
                    "willBeLate": gbr_prediction > 0,
                    "prediction": max(0, gbr_prediction)
                }
            ],
            "range_predictions": {
                "dates": date_predictions,
                "quantities": quantity_predictions
            },
            "metadata": {
                "input_params": {
                    "supplier": supplier,
                    "quantity": quantity,
                    "order_date": order_date
                }
            },
            "status_code": 200
        }
        
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in score_model: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "status_code": 500
            }),
            status_code=500,
            mimetype="application/json"
        )