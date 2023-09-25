import boto3

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("dish_recipes_db")

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    s3_file_name = event['Records'][0]['s3']['object']['key']

    resp = s3_client.get_object(Bucket=bucket_name,Key=s3_file_name)

    data = resp['Body'].read().decode("utf-8")

    dishes = data.split("\n")

    for i in dishes:
        print(i)
        dish = i.split(",")
        # try to insert data into DynamoDB table
        try:
            table.put_item(
                Item = {
                    "dish"        : dish[0],
                    "ingredients"       : dish[1],
                    "split_ingredients" : dish[3],
                    "quantities"   : dish[4],
                    "directions"   : dish[5]
                }
            )
        except Exception as e:
            print("Finished processing file")