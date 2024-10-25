aws dynamodb put-item \
    --table-name Users \
    --item '{
        "UserID": {"S": "b07d4732-6675-4a98-a45f-c2fa714262db"},
        "UserEmail": {"S": "darthShana@gmail.com"},
        "FirstName": {"S": "Dharshana"},
        "LastName": {"S": "Ratnayake"},
        "properties": {"L": [
            {
                "M": {
                    "property_id": {"S": "86fe1497-7595-428e-8b0e-feab35c278db"},
                    "address1": {"S": "34 Nicholas Gibbons Drive,"},
                    "suburb": {"S": "Clendon Park"},
                    "city": {"S": "Auckland"},
                    "property_type": {"S": "House"},
                    "bedrooms": {"N": "4"},
                    "assets": {"L": []}
                }
            }
        ]}
    }'