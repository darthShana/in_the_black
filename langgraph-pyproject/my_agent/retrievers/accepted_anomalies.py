from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

from my_agent.model.user import UserInfo
from my_agent.utils.aws_credentials import AWSSessionFactory

aws = AWSSessionFactory()
dynamodb = aws.get_session().resource('dynamodb')
table = dynamodb.Table('AcceptedAnomalies')


def accepted_anomalies(user: UserInfo, start_date: datetime, end_date: datetime):
    customer_attr = Attr('UserId')
    date_attr = Attr('Date')

    filter_expression = customer_attr.eq(user.user_id)
    filter_expression &= date_attr.between(start_date.strftime('%Y/%m/%d'), end_date.strftime('%Y/%m/%d'))

    response = table.scan(
        FilterExpression=filter_expression
    )

    return [{'period': r['Period'], 'anomaly': r['Insight'], 'reason': r['AcceptReason']} for r in response['Items']]
