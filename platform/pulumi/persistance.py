import pulumi_aws as aws
import pulumi


def create_dbs():
    basic_dynamodb_table = aws.dynamodb.Table("black_transactions",
        name="Transactions",
        billing_mode="PAY_PER_REQUEST",
        hash_key="TransactionID",
        attributes=[
            {
                "name": "TransactionID",
                "type": "S",
            },
            {
                "name": "CustomerNumber",
                "type": "S",
            }
        ],
        global_secondary_indexes=[{
            "name": "CustomerIndex",
            "hash_key": "CustomerNumber",
            "projection_type": "ALL"
        }],
        tags={
            "Name": "dynamodb-table-1",
            "Environment": "production",
        }
    )
    customer_assets = aws.dynamodb.Table("customer_assets",
        name="CustomerAssets",
        billing_mode="PAY_PER_REQUEST",
        hash_key="CustomerAssetsID",
        attributes=[
            {
                "name": "CustomerAssetsID",
                "type": "S",
            },
            {
                "name": "CustomerNumber",
                "type": "S",
            }
        ],
        global_secondary_indexes=[{
            "name": "CustomerIndex",
            "hash_key": "CustomerNumber",
            "projection_type": "ALL"
        }],
        tags={
            "Name": "customer_assets",
            "Environment": "production",
        }
    )

    return {
        'transactions': basic_dynamodb_table,
        'customer_assets': customer_assets
    }


pulumi.export('create_dbs', create_dbs)
