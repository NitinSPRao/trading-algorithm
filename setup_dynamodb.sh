#!/bin/bash

# DynamoDB Table Setup Script
# Region: us-east-2

echo "Setting up DynamoDB tables for trading algorithm..."

# Delete existing tables if they exist
echo "Checking for existing tables..."
aws dynamodb delete-table --table-name trading_state --region us-east-2 2>/dev/null || echo "trading_state table doesn't exist, continuing..."
aws dynamodb delete-table --table-name trading_events --region us-east-2 2>/dev/null || echo "trading_events table doesn't exist, continuing..."

echo "Waiting for table deletions to complete (if any)..."
sleep 10

# Create trading_state table
echo "Creating trading_state table..."
aws dynamodb create-table \
    --table-name trading_state \
    --attribute-definitions \
        AttributeName=trader_id,AttributeType=S \
    --key-schema \
        AttributeName=trader_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-2

# Create trading_events table
echo "Creating trading_events table..."
aws dynamodb create-table \
    --table-name trading_events \
    --attribute-definitions \
        AttributeName=event_date,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=event_date,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-2

echo "Waiting for tables to become active..."
aws dynamodb wait table-exists --table-name trading_state --region us-east-2
aws dynamodb wait table-exists --table-name trading_events --region us-east-2

echo "✓ Tables created successfully!"
echo ""
echo "Verifying tables..."
aws dynamodb describe-table --table-name trading_state --region us-east-2 --query 'Table.{Name:TableName,Status:TableStatus,Keys:KeySchema}' --output table
aws dynamodb describe-table --table-name trading_events --region us-east-2 --query 'Table.{Name:TableName,Status:TableStatus,Keys:KeySchema}' --output table

echo ""
echo "Setup complete!"
