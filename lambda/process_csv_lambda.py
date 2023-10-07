import boto3
import csv
import ast

# aws lambda invoke --function-name YourFunctionName \
#                   --payload '{"NEW_USER": "value1", "key2": "value2"}' \
#                   --cli-binary-format raw-in-base64-out response.json

# aws lambda invoke --function-name create_user response.json

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("dish_recipes_db")

def process_csv_lambda(event, context):
    print(f"event: {event}")

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    s3_file_name = event['Records'][0]['s3']['object']['key']

    resp = s3_client.get_object(Bucket=bucket_name,Key=s3_file_name)
    resp = resp['Body'].read().decode('utf-8').splitlines()

    lines = csv.reader(resp)

    # print(lines)
    print(f"type(lines): {type(lines)}")
    
    headers = next(lines)
    print('headers: %s' %(headers))
    
    for dish in lines:
        #print complete line
        print("dish: ", dish)
        print("dish[0]: ", dish[0])
        print("dish[1]: ", dish[1])
        print("dish[2]: ", dish[2])

        print(f"type(dish): {type(dish)}")
        
        try:
            table.put_item(
                Item = {
                    "id" : dish[0],
                    "uid": dish[1],
                    "dish"        : dish[2],
                    "ingredients"       : dish[3],
                    "split_ingredients" : dish[4],
                    "quantities"   : dish[5],
                    "directions"   : dish[6]
                }
            )
        except Exception as e:
            print("Finished processing file")

    # data = resp['Body'].read().decode("utf-8")
    # dishes = data.split('\n')

    # for i in range(1, len(dishes)):
    #     print(f"i: {i}")
    #     print(f"dishes[i]: {dishes[i]}")
        
    #     # row_lst = str(dishes2[i], 'UTF-8').split(",")
    #     # print(f"row_lst: {row_lst}")
        
    #     # # if length of row list is not expected, skip this iteration
    #     # if len(row_lst) == 1:
            
    #     #     print("row_lst length: ", len(row_lst))
            
    #     #     continue

    #     dish = dishes[i].split(",")
    #     # dish = i.split(",")
        
    #     print(f"dish: {dish}")

    #     # try to insert data into DynamoDB table
    #     try:
    #         table.put_item(
    #             Item = {
    #                 "id" : dish[0],
    #                 "dish"        : dish[1],
    #                 "ingredients"       : dish[2],
    #                 "split_ingredients" : dish[3],
    #                 "quantities"   : dish[4],
    #                 "directions"   : dish[5]
    #             }
    #         )
    #     except Exception as e:
    #         print("Finished processing file")
